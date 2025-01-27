import chromadb
from chromadb.config import Settings
from typing import Dict, List, Optional, Any, Union
import json
import logging
from datetime import datetime
from pathlib import Path
from .base import (
    VectorStoreProvider,
    VectorDocument,
    QueryResult,
    VectorStoreError
)
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class ChromaProvider(VectorStoreProvider):
    """Chroma vector store provider implementation"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.embedding_fn = None
        self.index_name = None
        self.dimension = None
    
    async def connect(self, config: Dict[str, Any]) -> None:
        """Initialize ChromaDB connection"""
        settings = chromadb.Settings(
            persist_directory=config.get('persist_path', './chroma_db'),
            is_persistent=config.get('persist', True)
        )
        
        self.client = chromadb.Client(settings)
        self.embedding_fn = config.get(
            'embedding_fn',
            embedding_functions.DefaultEmbeddingFunction()
        )
        
        self.collection = self.client.get_or_create_collection(
            name=config.get('collection_name', 'main'),
            embedding_function=self.embedding_fn
        )
        
        self.index_name = config.get('collection_name', 'main')
        self.dimension = config.get('dimension', 128)
        
        logger.info(f"Successfully initialized Chroma collection: {self.index_name}")
    
    async def add_documents(
        self,
        documents: List[VectorDocument],
        batch_size: int = 100
    ) -> List[str]:
        """Add documents to Chroma collection"""
        try:
            if not self.collection:
                raise VectorStoreError("Chroma collection not initialized")
            
            # Prepare documents for addition
            ids = []
            embeddings = []
            metadatas = []
            documents_data = []
            
            for doc in documents:
                if not doc.embedding or len(doc.embedding) != self.dimension:
                    raise VectorStoreError(
                        f"Invalid embedding dimension for document {doc.id}"
                    )
                
                # Convert content to string if bytes
                content = (
                    doc.content.decode() if isinstance(doc.content, bytes)
                    else doc.content
                )
                
                ids.append(doc.id)
                embeddings.append(doc.embedding)
                metadatas.append({
                    **doc.metadata,
                    "_timestamp": doc.timestamp.isoformat()
                })
                documents_data.append(content)
            
            # Add documents in batches
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_documents = documents_data[i:i + batch_size]
                
                self.collection.add(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    metadatas=batch_metadatas,
                    documents=batch_documents
                )
            
            logger.info(f"Added {len(documents)} documents to Chroma")
            return ids
            
        except Exception as e:
            logger.error(f"Error adding documents to Chroma: {str(e)}")
            raise VectorStoreError(f"Failed to add documents: {str(e)}")
    
    async def query(
        self,
        query_embedding: List[float],
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        min_score: float = 0.0
    ) -> List[QueryResult]:
        """Query Chroma collection"""
        try:
            if not self.collection:
                raise VectorStoreError("Chroma collection not initialized")
            
            # Prepare filter if provided
            where = filter_metadata if filter_metadata else None
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
                include=["metadatas", "documents", "distances"]
            )
            
            # Convert results to QueryResult objects
            query_results = []
            for i in range(len(results["ids"][0])):
                # Convert distance to similarity score (Chroma uses L2 distance)
                distance = results["distances"][0][i]
                score = 1.0 / (1.0 + distance)  # Convert to similarity score
                
                if score < min_score:
                    continue
                
                metadata = results["metadatas"][0][i]
                timestamp = datetime.fromisoformat(metadata.pop("_timestamp"))
                
                doc = VectorDocument(
                    id=results["ids"][0][i],
                    content=results["documents"][0][i],
                    metadata=metadata,
                    timestamp=timestamp
                )
                
                query_results.append(QueryResult(
                    document=doc,
                    score=score
                ))
            
            logger.info(f"Found {len(query_results)} matching documents in Chroma")
            return query_results
            
        except Exception as e:
            logger.error(f"Error querying Chroma: {str(e)}")
            raise VectorStoreError(f"Failed to query collection: {str(e)}")
    
    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from Chroma collection"""
        try:
            if not self.collection:
                raise VectorStoreError("Chroma collection not initialized")
            
            self.collection.delete(ids=document_ids)
            logger.info(f"Deleted {len(document_ids)} documents from Chroma")
            
        except Exception as e:
            logger.error(f"Error deleting documents from Chroma: {str(e)}")
            raise VectorStoreError(f"Failed to delete documents: {str(e)}")
    
    async def update_metadata(
        self,
        document_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Update document metadata in Chroma"""
        try:
            if not self.collection:
                raise VectorStoreError("Chroma collection not initialized")
            
            # Get existing document
            doc = await self.get_document(document_id)
            if not doc:
                raise VectorStoreError(f"Document not found: {document_id}")
            
            # Update metadata
            doc.metadata.update(metadata)
            
            # Update in Chroma
            self.collection.update(
                ids=[document_id],
                metadatas=[{
                    **doc.metadata,
                    "_timestamp": doc.timestamp.isoformat()
                }]
            )
            
            logger.info(f"Updated metadata for document: {document_id}")
            
        except Exception as e:
            logger.error(f"Error updating metadata in Chroma: {str(e)}")
            raise VectorStoreError(f"Failed to update metadata: {str(e)}")
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Get document from Chroma by ID"""
        try:
            if not self.collection:
                raise VectorStoreError("Chroma collection not initialized")
            
            # Get document
            result = self.collection.get(
                ids=[document_id],
                include=["metadatas", "documents"]
            )
            
            if not result["ids"]:
                return None
            
            # Convert to VectorDocument
            metadata = result["metadatas"][0]
            timestamp = datetime.fromisoformat(metadata.pop("_timestamp"))
            
            return VectorDocument(
                id=document_id,
                content=result["documents"][0],
                metadata=metadata,
                timestamp=timestamp
            )
            
        except Exception as e:
            logger.error(f"Error getting document from Chroma: {str(e)}")
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
        """Cleanup Chroma resources"""
        try:
            if self.client:
                # Persist data
                self.client.persist()
                
                # Reset instance variables
                self.client = None
                self.collection = None
                self.embedding_fn = None
                self.index_name = None
                self.dimension = None
            
            logger.info("Cleaned up Chroma resources")
            
        except Exception as e:
            logger.error(f"Error cleaning up Chroma resources: {str(e)}")
            raise VectorStoreError(f"Failed to cleanup resources: {str(e)}")

    async def query_memory(self, query: str, top_k: int = 5) -> List[VectorDocument]:
        """Query using text input with automatic embedding"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=['documents', 'embeddings', 'metadatas']
        )
        
        return [
            VectorDocument(
                id=results['ids'][0][i],
                content=results['documents'][0][i],
                metadata=results['metadatas'][0][i],
                embedding=results['embeddings'][0][i]
            )
            for i in range(len(results['ids'][0]))
        ] 