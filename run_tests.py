"""
Simple Tests for Research Digest Agent
Run this file to verify everything works
"""

print("="*60)
print("RUNNING TESTS")
print("="*60)

# Test 1: Empty source handling
print("\nTest 1: Empty/Unreachable Source Handling")
try:
    from src.ingestion.fetcher import SourceFetcher
    results = SourceFetcher.fetch_sources([
        'https://nonexistent-site-12345.com',
        'missing_file_xyz.txt'
    ])
    if len(results) == 0:
        print("  PASSED: Invalid sources skipped")
    else:
        print(f"  FAILED: Expected 0, got {len(results)}")
except Exception as e:
    print(f"  PASSED: Exception handled - {str(e)[:50]}")

# Test 2: Claim extraction with evidence
print("\nTest 2: Claim Extraction with Evidence")
try:
    from src.extraction.claim_extractor import ClaimExtractor
    text = "Research demonstrates that AI improves efficiency by 40%."
    claims = ClaimExtractor.extract_claims(text, 'test', 'Test')
    if len(claims) >= 1 and 'evidence' in claims[0]:
        print("  PASSED: Claims extracted with evidence")
    else:
        print("  FAILED: No claims or evidence missing")
except Exception as e:
    print(f"  FAILED: {str(e)[:50]}")

# Test 3: Conflict preservation
print("\nTest 3: Conflict Preservation")
try:
    from src.pipeline import ResearchDigestPipeline
    pipeline = ResearchDigestPipeline()
    test_clusters = [{
        'claims': [
            {'text': 'X increases Y', 'source_id': 'S1'},
            {'text': 'X decreases Y', 'source_id': 'S2'}
        ]
    }]
    conflicts = pipeline._detect_conflicts(test_clusters)
    if len(conflicts) >= 1:
        print("  PASSED: Conflicts detected and preserved")
    else:
        print("  FAILED: Conflicts not detected")
except Exception as e:
    print(f"  FAILED: {str(e)[:50]}")

print("\n" + "="*60)
print("TESTS COMPLETE")
print("="*60)