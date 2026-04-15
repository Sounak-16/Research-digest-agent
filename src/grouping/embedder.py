from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SemanticEmbedder:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
    
    def embed_claims(self, claims: List[Dict]) -> np.ndarray:
        texts = [c['text'] for c in claims]
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings