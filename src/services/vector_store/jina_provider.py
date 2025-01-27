from typing import List, Dict
from docarray import Document, DocumentArray
from jina import Client
import numpy as np
from .base_provider import VectorStoreProvider
from ..models import AVComponent

class JinaVectorStore(VectorStoreProvider):
    def __init__(self, endpoint: str):
        self.client = Client(host=endpoint)
        self.dimension = 512  # Matches our component embeddings
        
    async def index_components(self, components: List[AVComponent]) -> None:
        docs = DocumentArray()
        for comp in components:
            doc = Document(
                text=comp.description,
                tags={
                    'id': comp.id,
                    'type': comp.type,
                    'manufacturer': comp.manufacturer
                }
            )
            doc.embedding = self._generate_embedding(comp)
            docs.append(doc)
            
        await self.client.post('/index', docs)
        
    async def search_similar(self, query_component: AVComponent, limit: int = 5) -> List[Dict]:
        query_doc = Document(
            text=query_component.description,
            embedding=self._generate_embedding(query_component)
        )
        
        results = await self.client.post(
            '/search',
            query_doc,
            parameters={'limit': limit}
        )
        
        return [{
            'id': match.tags['id'],
            'score': float(match.scores['cosine'].value),
            'type': match.tags['type']
        } for match in results[0].matches]
        
    def _generate_embedding(self, component: AVComponent) -> np.ndarray:
        # Combine component attributes for embedding
        text = f"{component.type} {component.manufacturer} {component.description}"
        return self.client.post('/encode', Document(text=text)).embeddings[0] 