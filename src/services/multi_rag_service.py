from typing import Dict, List, Optional

class MultiRAGService:
    """Manages multiple RAG collections"""
    def __init__(self, rag_service):
        self.rag_service = rag_service
        self.collections = {}
        
    async def create_collection(self, name: str, description: str = "") -> None:
        """Create a new RAG collection"""
        self.collections[name] = {
            "description": description,
            "index": await self.rag_service.create_index(name)
        }
        
    async def store_in_collection(self, collection_name: str, content: str, metadata: Dict) -> None:
        """Store content in a specific collection"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
        await self.rag_service.store_memory(
            content=content,
            metadata=metadata,
            index_name=collection_name
        )
        
    async def query_collection(self, collection_name: str, query: str) -> List[Dict]:
        """Query a specific collection"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
        return await self.rag_service.query_memory(
            query,
            index_name=collection_name
        ) 