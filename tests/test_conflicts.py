def test_conflict_preservation():
    from src.pipeline import ResearchDigestPipeline
    pipeline = ResearchDigestPipeline()
    clusters = [{
        'theme_label': 'effect',
        'claims': [
            {'text': 'X increases Y', 'source_id': 'S1', 'confidence': 0.8},
            {'text': 'X decreases Y', 'source_id': 'S2', 'confidence': 0.7}
        ]
    }]
    conflicts = pipeline._detect_conflicts(clusters)
    assert len(conflicts) == 1
    assert 'increase' in conflicts[0]['view_1']
    assert 'decrease' in conflicts[0]['view_2']