from typing import List, Dict
from docarray import Document, DocumentArray
from jina import Client
from jina.excepts import BadClient, BadServer
import numpy as np
import logging
from .base_provider import VectorStoreProvider
from ..models import AVComponent
from config.jina_settings import JinaConfig
from pydantic import ValidationError

class JinaVectorStore(VectorStoreProvider):
    def __init__(self, config: JinaConfig = JinaConfig()):
        self.config = config
        self.client = Client(host=config.endpoint)
        self.logger = logging.getLogger(__name__)
        self._validate_connection()
        self.dimension = config.embedding_dim  # Use config value
        
    def _validate_connection(self):
        try:
            self.client.post('/dry_run', timeout=500)
        except (BadClient, BadServer) as e:
            raise ConnectionError(f"Failed to connect to Jina server: {e}") from e

    async def index_components(self, components: List[AVComponent]) -> None:
        try:
            docs = DocumentArray(
                Document(
                    text=comp.description,
                    tags=comp.dict(),
                    embedding=await self._generate_embedding(comp)
                ) for comp in components
            )
            await self.client.post(
                '/index', 
                docs,
                parameters={'batch_size': 100},
                timeout=300
            )
        except Exception as e:
            self.logger.error(f"Indexing failed: {str(e)}")
            raise
        
    async def search_similar(self, query_component: AVComponent, limit: int = 5) -> List[Dict]:
        query_doc = Document(
            text=query_component.description,
            embedding=await self._generate_embedding(query_component)
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
        
    async def _generate_embedding(self, component: AVComponent) -> np.ndarray:
        try:
            result = await self.client.post(
                '/encode', 
                Document(text=f"{component.type} {component.manufacturer} {component.description}"),
                timeout=self.config.timeout
            )
            return result.embeddings[0]
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {str(e)}")
            raise 