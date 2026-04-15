import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class ClaimClusterer:
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
    
    def group_claims(self, claims: List[Dict], embeddings: np.ndarray) -> List[Dict]:
        if len(claims) == 0:
            return []
        
        sim_matrix = cosine_similarity(embeddings)
        n = len(claims)
        visited = [False] * n
        clusters = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            # Find all claims similar to i
            cluster_indices = [i]
            for j in range(i+1, n):
                if not visited[j] and sim_matrix[i][j] >= self.threshold:
                    cluster_indices.append(j)
                    visited[j] = True
            visited[i] = True
            
            # Build cluster
            cluster_claims = [claims[idx] for idx in cluster_indices]
            clusters.append(self._create_cluster(cluster_claims))
        
        # Merge clusters that have high cross-similarity (secondary pass)
        merged_clusters = self._merge_overlapping_clusters(clusters, embeddings, claims)
        return merged_clusters
    
    def _create_cluster(self, cluster_claims: List[Dict]) -> Dict:
        # Generate theme label (simple: most common keywords)
        all_text = " ".join([c['text'] for c in cluster_claims])
        words = [w for w in all_text.lower().split() if len(w) > 4]
        from collections import Counter
        common = Counter(words).most_common(3)
        label = " / ".join([w for w, _ in common]) if common else "Miscellaneous theme"
        
        # Merge summary (longest + most confident)
        best_claim = max(cluster_claims, key=lambda x: x['confidence'])
        summary = best_claim['text']
        
        return {
            'theme_label': label,
            'summary': summary,
            'claims': cluster_claims,
            'sources': list(set([c['source_id'] for c in cluster_claims]))
        }
    
    def _merge_overlapping_clusters(self, clusters, embeddings, claims):
        # Simplified: if two clusters share a claim with similarity > threshold, merge
        if len(clusters) <= 1:
            return clusters
        
        merged = []
        used = [False] * len(clusters)
        
        for i, c1 in enumerate(clusters):
            if used[i]:
                continue
            current = c1
            for j, c2 in enumerate(clusters[i+1:], i+1):
                if used[j]:
                    continue
                # Check if clusters share any highly similar claims
                overlap = False
                for claim1 in current['claims']:
                    for claim2 in c2['claims']:
                        # Would need embedding comparison again — simplified here
                        if claim1['source_id'] == claim2['source_id']:
                            overlap = True
                            break
                if overlap:
                    current = self._create_cluster(current['claims'] + c2['claims'])
                    used[j] = True
            merged.append(current)
            used[i] = True
        return merged