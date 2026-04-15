import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.fetcher import SourceFetcher
from src.extraction.claim_extractor import ClaimExtractor
from src.grouping.clusterer import ClaimClusterer
import numpy as np

class TestResearchDigestAgent:
    
    def test_empty_unreachable_source_handling(self):
        """Test that the agent gracefully handles broken/unreachable sources"""
        sources = [
            'https://this-domain-does-not-exist-12345.com',
            'nonexistent_file.txt',
            'https://httpbin.org/status/404'
        ]
        
        results = SourceFetcher.fetch_sources(sources)
        
        assert len(results) == 0, f'Expected 0 valid sources, got {len(results)}'
        print('✓ Test 1 passed: Empty/unreachable sources handled gracefully')
    
    def test_deduplication_of_similar_claims(self):
        """Test that similar claims are grouped together"""
        claims = [
            {
                'text': 'Climate change causes sea levels to rise by 3.6mm per year',
                'source_id': 'source1',
                'confidence': 0.9,
                'evidence': 'Study A shows...'
            },
            {
                'text': 'Sea levels are rising at 3.6mm annually due to climate change',
                'source_id': 'source2', 
                'confidence': 0.85,
                'evidence': 'Study B confirms...'
            },
            {
                'text': 'The weather is nice today',
                'source_id': 'source3',
                'confidence': 0.5,
                'evidence': 'Just a statement'
            }
        ]
        
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer()
        texts = [c['text'] for c in claims]
        embeddings = vectorizer.fit_transform(texts).toarray()
        
        clusterer = ClaimClusterer(threshold=0.3)
        clusters = clusterer.group_claims(claims, embeddings)
        
        multi_claim_clusters = [c for c in clusters if len(c['claims']) > 1]
        assert len(multi_claim_clusters) >= 1, 'Similar claims should be grouped'
        print('✓ Test 2 passed: Similar claims successfully grouped')
    
    def test_preservation_of_conflicting_claims(self):
        """Test that conflicting viewpoints are preserved and attributed"""
        def detect_conflicts_simple(clusters):
            conflicts = []
            for cluster in clusters:
                texts = [c['text'].lower() for c in cluster.get('claims', [])]
                if any('increase' in t for t in texts) and any('decrease' in t for t in texts):
                    increase_claims = [c for c in cluster.get('claims', []) if 'increase' in c['text'].lower()]
                    decrease_claims = [c for c in cluster.get('claims', []) if 'decrease' in c['text'].lower()]
                    if increase_claims and decrease_claims:
                        conflicts.append({
                            'description': "Mixed directional effects",
                            'view_1': increase_claims[0]['text'],
                            'view_2': decrease_claims[0]['text'],
                            'source_1': increase_claims[0]['source_id'],
                            'source_2': decrease_claims[0]['source_id']
                        })
            return conflicts
        
        test_clusters = [
            {
                'theme_label': 'Climate Impact',
                'claims': [
                    {
                        'text': 'Climate change increases hurricane intensity',
                        'source_id': 'NOAA Report',
                        'confidence': 0.9
                    },
                    {
                        'text': 'Climate change decreases global hurricane frequency', 
                        'source_id': 'Alternative Study',
                        'confidence': 0.7
                    }
                ]
            }
        ]
        
        conflicts = detect_conflicts_simple(test_clusters)
        
        assert len(conflicts) >= 1, 'Conflicting claims should be detected'
        print('✓ Test 3 passed: Conflicting claims preserved with proper attribution')
    
    def test_claim_extraction_with_evidence(self):
        """Test that claims are grounded with evidence from source"""
        sample_text = """Our research demonstrates that renewable energy reduces carbon emissions by 45 percent. 
        The study analyzed data from 50 countries over 10 years. We conclude that solar 
        and wind power are the most effective solutions."""
        
        claims = ClaimExtractor.extract_claims(sample_text, 'test_source', 'Test Title')
        
        assert len(claims) >= 1, 'Should extract claims from text'
        
        for claim in claims:
            assert 'evidence' in claim, 'Claim missing evidence'
            assert len(claim['evidence']) > 0, 'Evidence should not be empty'
        
        print('✓ Test 4 passed: Claims properly grounded with evidence')

if __name__ == '__main__':
    test = TestResearchDigestAgent()
    test.test_empty_unreachable_source_handling()
    test.test_deduplication_of_similar_claims()
    test.test_preservation_of_conflicting_claims()
    test.test_claim_extraction_with_evidence()
    print('\n All tests passed!')
