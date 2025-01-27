from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class VectorDocument(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]

class VectorStoreProvider(ABC):
    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> None:
        """Initialize connection to vector database"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        """Store documents with embeddings"""
        pass
    
    @abstractmethod
    async def query_memory(self, query: str, top_k: int = 5) -> List[VectorDocument]:
        """Semantic search with natural language query"""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> None:
        """Remove documents by IDs"""
        pass
    
    @abstractmethod
    async def update_document(self, document_id: str, 
                            content: str, metadata: Dict[str, Any]) -> None:
        """Update document content and metadata"""
        pass 