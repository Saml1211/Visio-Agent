from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingGenerator:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a text query"""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch generate embeddings"""
        return self.model.encode(texts).tolist()
    
    @staticmethod
    def normalize(vector: List[float]) -> List[float]:
        """Normalize vector to unit length"""
        arr = np.array(vector)
        norm = np.linalg.norm(arr)
        return (arr / norm).tolist() 