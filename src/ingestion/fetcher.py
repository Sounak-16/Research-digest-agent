import requests
from pathlib import Path
from urllib.parse import urlparse
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SourceFetcher:
    @staticmethod
    def fetch_sources(sources: List[str]) -> List[Dict]:
        """Fetch content from URLs or local files, skipping invalid ones."""
        results = []
        for src in sources:
            try:
                if src.startswith(('http://', 'https://')):
                    data = SourceFetcher._fetch_url(src)
                else:
                    data = SourceFetcher._fetch_file(src)
                
                if data:
                    results.append(data)
                else:
                    logger.warning(f"Skipping empty/unreadable source: {src}")
            except Exception as e:
                logger.error(f"Failed to fetch {src}: {e}")
        return results

    @staticmethod
    def _fetch_url(url: str, timeout: int = 10) -> Optional[Dict]:
        try:
            resp = requests.get(url, timeout=timeout, headers={'User-Agent': 'ResearchDigestAgent/1.0'})
            resp.raise_for_status()
            return {
                'source_id': url,
                'source_type': 'url',
                'raw_content': resp.text,
                'title': SourceFetcher._extract_title(resp.text)
            }
        except Exception as e:
            logger.error(f"URL fetch error {url}: {e}")
            return None

    @staticmethod
    def _fetch_file(path: str) -> Optional[Dict]:
        p = Path(path)
        if not p.exists():
            logger.error(f"File not found: {path}")
            return None
        try:
            raw = p.read_text(encoding='utf-8')
            return {
                'source_id': str(p.absolute()),
                'source_type': 'file',
                'raw_content': raw,
                'title': p.stem
            }
        except Exception as e:
            logger.error(f"File read error {path}: {e}")
            return None

    @staticmethod
    def _extract_title(html: str) -> str:
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            return soup.title.string.strip() if soup.title and soup.title.string else "No title"
        except:
            return "No title"