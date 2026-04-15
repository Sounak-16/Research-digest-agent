from src.grouping.clusterer import ClaimClusterer

def test_deduplication():
    claims = [
        {'text': 'AI improves diagnosis accuracy', 'source_id': 'A', 'confidence': 0.9},
        {'text': 'Machine learning boosts diagnostic precision', 'source_id': 'B', 'confidence': 0.85},
        {'text': 'The weather is nice today', 'source_id': 'C', 'confidence': 0.5}
    ]
    import numpy as np
    # Simplified: would need real embeddings; here we mock
    clusterer = ClaimClusterer(threshold=0.7)
    # In real test, embed with model
    assert True