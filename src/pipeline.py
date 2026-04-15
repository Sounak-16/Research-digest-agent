import logging
from pathlib import Path
from src.ingestion.fetcher import SourceFetcher
from src.ingestion.reader import TextCleaner
from src.extraction.claim_extractor import ClaimExtractor
from src.grouping.embedder_lightweight import SemanticEmbedder
from src.grouping.clusterer import ClaimClusterer
from src.outputs.digest_generator import DigestGenerator
from src.outputs.json_serializer import JSONSerializer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchDigestPipeline:
    def __init__(self, similarity_threshold: float = 0.75):
        self.threshold = similarity_threshold
        self.embedder = SemanticEmbedder()
        self.clusterer = ClaimClusterer(threshold=similarity_threshold)
    
    def run(self, sources: list, output_dir: str = "./outputs"):
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. Ingestion
        logger.info(f"Ingesting {len(sources)} sources...")
        source_data = SourceFetcher.fetch_sources(sources)
        logger.info(f"Successfully ingested {len(source_data)} sources")
        
        # 2. Clean and extract claims
        all_claims = []
        sources_metadata = []
        for src in source_data:
            cleaned = TextCleaner.clean(src['raw_content'], src['source_type'])
            sources_metadata.append({
                'source_id': src['source_id'],
                'title': src['title'],
                'content_length': len(cleaned),
                'source_type': src['source_type']
            })
            claims = ClaimExtractor.extract_claims(cleaned, src['source_id'], src['title'])
            all_claims.extend(claims)
        
        logger.info(f"Extracted {len(all_claims)} total claims")
        
        # 3. Embed and cluster
        if len(all_claims) > 0:
            embeddings = self.embedder.embed_claims(all_claims)
            clusters = self.clusterer.group_claims(all_claims, embeddings)
        else:
            clusters = []
        
        # 4. Detect conflicts (claims with opposite stance on similar topic)
        conflicting = self._detect_conflicts(clusters)
        
        # 5. Generate outputs
        digest = DigestGenerator.generate(clusters, conflicting, len(source_data))
        with open(f"{output_dir}/digest.md", 'w', encoding='utf-8') as f:
            f.write(digest)
        
        JSONSerializer.serialize(sources_metadata, all_claims, f"{output_dir}/sources.json")
        
        logger.info(f"Pipeline complete. Outputs in {output_dir}")
        return clusters, conflicting
    
    def _detect_conflicts(self, clusters):
        # Simplified conflict detection: if cluster has claims with opposite keywords
        conflicts = []
        for cluster in clusters:
            texts = [c['text'].lower() for c in cluster['claims']]
            if any('increase' in t for t in texts) and any('decrease' in t for t in texts):
                conflicts.append({
                    'description': f"Mixed directional effects for theme '{cluster['theme_label']}'",
                    'view_1': next(c['text'] for c in cluster['claims'] if 'increase' in c['text'].lower()),
                    'view_2': next(c['text'] for c in cluster['claims'] if 'decrease' in c['text'].lower()),
                    'source_1': next(c['source_id'] for c in cluster['claims'] if 'increase' in c['text'].lower()),
                    'source_2': next(c['source_id'] for c in cluster['claims'] if 'decrease' in c['text'].lower())
                })
        return conflicts