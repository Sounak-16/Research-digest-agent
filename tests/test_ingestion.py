import pytest
from src.ingestion.fetcher import SourceFetcher

def test_broken_url_handling():
    result = SourceFetcher.fetch_sources(["https://this-domain-does-not-exist-12345.com"])
    assert len(result) == 0

def test_empty_file_handling(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("")
    result = SourceFetcher.fetch_sources([str(empty)])
    assert len(result) == 1
    assert len(result[0]['raw_content']) == 0