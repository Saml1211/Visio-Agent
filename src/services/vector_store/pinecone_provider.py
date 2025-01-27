import pinecone
from typing import Dict, List, Optional, Any, Union
import asyncio
import json
import logging
from datetime import datetime
from .base import (
    VectorStoreProvider,
    VectorDocument,
    QueryResult,
    VectorStoreError
)

logger = logging.getLogger(__name__)

class PineconeProvider(VectorStoreProvider):
    """Pinecone vector store provider implementation"""
    
    def __init__(self):
        self.index = None
        self.index_name = None
        self.dimension = None
        
    async def connect(self, config: Dict[str, Any]) -> None:
        pinecone.init(
            api_key=config['api_key'],
            environment=config['environment']
        )
        self.index = pinecone.Index(config['index_name'])
    
    async def add_documents(self, documents: List[VectorDocument]) -> List[str]:
        vectors = []
        ids = []
        for doc in documents:
            vector_id = f"doc_{doc.id}"
            vectors.append((vector_id, doc.embedding, doc.metadata))
            ids.append(vector_id)
        self.index.upsert(vectors=vectors)
        return ids
    
    async def query(
        self,
        query_embedding: List[float],
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[QueryResult]:
        """Query Pinecone index"""
        try:
            if not self.index:
                raise VectorStoreError("Pinecone index not initialized")
            
            # Prepare filter if provided
            filter_dict = None
            if filter_metadata:
                filter_dict = {
                    f"metadata.{k}": json.dumps(v)
                    for k, v in filter_metadata.items()
                }
            
            # Query index
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.index.query(
                    vector=query_embedding,
                    top_k=limit,
                    include_metadata=True,
                    filter=filter_dict
                )
            )
            
            # Convert results to QueryResult objects
            query_results = []
            for match in results.matches:
                if match.score < min_score:
                    continue
                
                metadata = json.loads(match.metadata["metadata"])
                content = match.metadata["content"]
                timestamp = datetime.fromisoformat(match.metadata["timestamp"])
                
                doc = VectorDocument(
                    id=match.id,
                    content=content,
                    metadata=metadata,
                    embedding=match.values,
                    timestamp=timestamp
                )
                
                query_results.append(QueryResult(
                    document=doc,
                    score=match.score
                ))
            
            logger.info(f"Found {len(query_results)} matching documents in Pinecone")
            return query_results
            
        except Exception as e:
            logger.error(f"Error querying Pinecone: {str(e)}")
            raise VectorStoreError(f"Failed to query index: {str(e)}")
    
    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from Pinecone index"""
        try:
            if not self.index:
                raise VectorStoreError("Pinecone index not initialized")
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.index.delete,
                document_ids
            )
            
            logger.info(f"Deleted {len(document_ids)} documents from Pinecone")
            
        except Exception as e:
            logger.error(f"Error deleting documents from Pinecone: {str(e)}")
            raise VectorStoreError(f"Failed to delete documents: {str(e)}")
    
    async def update_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update document metadata in Pinecone"""
        try:
            if not self.index:
                raise VectorStoreError("Pinecone index not initialized")
            
            # Get existing document
            doc = await self.get_document(document_id)
            if not doc:
                raise VectorStoreError(f"Document not found: {document_id}")
            
            # Update metadata
            doc.metadata.update(metadata)
            
            # Update in Pinecone
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.index.update,
                document_id,
                metadata={"metadata": json.dumps(doc.metadata)}
            )
            
            logger.info(f"Updated metadata for document: {document_id}")
            
        except Exception as e:
            logger.error(f"Error updating metadata in Pinecone: {str(e)}")
            raise VectorStoreError(f"Failed to update metadata: {str(e)}")
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Get document from Pinecone by ID"""
        try:
            if not self.index:
                raise VectorStoreError("Pinecone index not initialized")
            
            # Fetch document
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.index.fetch([document_id])
            )
            
            if not result.vectors:
                return None
            
            # Convert to VectorDocument
            vector = result.vectors[document_id]
            metadata = json.loads(vector.metadata["metadata"])
            content = vector.metadata["content"]
            timestamp = datetime.fromisoformat(vector.metadata["timestamp"])
            
            return VectorDocument(
                id=document_id,
                content=content,
                metadata=metadata,
                embedding=vector.values,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error getting document from Pinecone: {str(e)}")
            raise VectorStoreError(f"Failed to get document: {str(e)}")
    
    async def validate_schema(
        self,
        schema: Dict[str, Any],
        document: VectorDocument
    ) -> List[str]:
        """Validate document against schema"""
        errors = []
        
        try:
            # Validate required fields
            for field, field_schema in schema.items():
                if field_schema.get("required", False):
                    if field not in document.metadata:
                        errors.append(f"Missing required field: {field}")
                        continue
                    
                    # Validate field type
                    field_type = field_schema.get("type")
                    if field_type:
                        value = document.metadata[field]
                        if field_type == "string" and not isinstance(value, str):
                            errors.append(f"Field {field} must be a string")
                        elif field_type == "number" and not isinstance(value, (int, float)):
                            errors.append(f"Field {field} must be a number")
                        elif field_type == "boolean" and not isinstance(value, bool):
                            errors.append(f"Field {field} must be a boolean")
                        elif field_type == "array" and not isinstance(value, list):
                            errors.append(f"Field {field} must be an array")
                        elif field_type == "object" and not isinstance(value, dict):
                            errors.append(f"Field {field} must be an object")
                
                # Validate enum values
                if "enum" in field_schema and field in document.metadata:
                    value = document.metadata[field]
                    if value not in field_schema["enum"]:
                        errors.append(
                            f"Invalid value for {field}. "
                            f"Must be one of: {field_schema['enum']}"
                        )
                
                # Validate string patterns
                if (
                    field_schema.get("type") == "string"
                    and "pattern" in field_schema
                    and field in document.metadata
                ):
                    import re
                    value = document.metadata[field]
                    if not re.match(field_schema["pattern"], value):
                        errors.append(
                            f"Field {field} does not match pattern: "
                            f"{field_schema['pattern']}"
                        )
            
            if errors:
                logger.warning(
                    f"Schema validation failed for document {document.id}: {errors}"
                )
            
            return errors
            
        except Exception as e:
            logger.error(f"Error validating schema: {str(e)}")
            raise VectorStoreError(f"Failed to validate schema: {str(e)}")
    
    async def cleanup(self) -> None:
        """Cleanup Pinecone resources"""
        try:
            if self.index:
                # No explicit cleanup needed for Pinecone
                self.index = None
                self.index_name = None
                self.dimension = None
                
            logger.info("Cleaned up Pinecone resources")
            
        except Exception as e:
            logger.error(f"Error cleaning up Pinecone resources: {str(e)}")
            raise VectorStoreError(f"Failed to cleanup resources: {str(e)}")

    async def query_memory(self, query: str, top_k: int = 5) -> List[VectorDocument]:
        # Implementation requires query embedding
        raise NotImplementedError("Query requires embedding generation")
    
    async def update_document(self, document_id: str, 
                            content: str, metadata: Dict[str, Any]) -> None:
        self.index.update(
            id=document_id,
            metadata=metadata
        ) 