from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class VectorDocument:
    """Base class for vector store documents"""
    id: str
    content: Union[str, bytes]
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: datetime = datetime.utcnow()

@dataclass
class QueryResult:
    """Result from a vector store query"""
    document: VectorDocument
    score: float

class VectorStoreError(Exception):
    """Base exception for vector store errors"""
    pass

class VectorStoreProvider(ABC):
    """Abstract base class for vector store providers"""
    
    @abstractmethod
    async def initialize(
        self,
        connection_params: Dict[str, Any],
        index_name: str,
        dimension: int
    ) -> None:
        """Initialize the vector store connection and index"""
        pass
    
    @abstractmethod
    async def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to the vector store"""
        pass
    
    @abstractmethod
    async def query(
        self,
        query_embedding: List[float],
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[QueryResult]:
        """Query the vector store"""
        pass
    
    @abstractmethod
    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the vector store"""
        pass
    
    @abstractmethod
    async def update_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update document metadata"""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Get a document by ID"""
        pass
    
    @abstractmethod
    async def validate_schema(
        self,
        schema: Dict[str, Any],
        document: VectorDocument
    ) -> List[str]:
        """Validate a document against a schema"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources"""
        pass 