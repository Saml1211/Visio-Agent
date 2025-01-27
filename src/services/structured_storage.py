from typing import Dict, Any, List
from datetime import datetime

class StructuredStorage:
    """Handles storage of structured data in RAG memory"""
    def __init__(self, rag_service):
        self.rag_service = rag_service
        
    async def store_structured_data(self, data: Dict[str, Any], user_id: str, tags: List[str] = []) -> None:
        """Store structured data with metadata"""
        await self.rag_service.store_memory(
            content=data,
            metadata={
                "user_id": user_id,
                "timestamp": datetime.now(),
                "source": "structured_data",
                "tags": tags
            }
        )
        
    async def search_structured_data(self, query: str, tags: List[str] = []) -> List[Dict]:
        """Search structured data with optional tags"""
        results = await self.rag_service.query_memory(query)
        return [
            result for result in results
            if any(tag in result.get("metadata", {}).get("tags", []) for tag in tags)
        ] 