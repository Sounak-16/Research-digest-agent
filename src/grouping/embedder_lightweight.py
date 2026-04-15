from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SemanticEmbedder:
    def __init__(self, model_name=None):
        logger.info("Using lightweight TF-IDF embedder (no PyTorch needed)")
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    
    def embed_claims(self, claims):
        texts = [c['text'] for c in claims]
        if len(texts) == 0:
            return np.array([])
        embeddings = self.vectorizer.fit_transform(texts).toarray()
        logger.info(f"Created {embeddings.shape[1]}-dimensional embeddings")
        return embeddings