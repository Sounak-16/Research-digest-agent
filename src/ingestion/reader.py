import re
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    @staticmethod
    def clean(raw_content, source_type):
        if source_type == 'url':
            soup = BeautifulSoup(raw_content, 'html.parser')
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            text = soup.get_text(separator=' ')
        else:
            text = raw_content
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        if len(text) < 100:
            logger.warning(f"Very short content after cleaning: {len(text)} chars")
        
        return text
