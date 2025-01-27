import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
import lilac as ll
import numpy as np
import io
from PIL import Image
import base64
from datetime import datetime
from .ai_service_config import AIServiceManager
import json
from .vector_store import (
    VectorStoreFactory,
    VectorStoreType,
    VectorDocument,
    QueryResult,
    VectorStoreError
)

logger = logging.getLogger(__name__)

@dataclass
class DocumentSchema:
    """Schema definition for documents"""
    fields: Dict[str, Dict[str, Any]]
    version: str
    description: Optional[str] = None

@dataclass
class ImageData:
    """Container for image data and metadata"""
    data: bytes
    format: str
    width: int
    height: int
    ocr_text: Optional[str] = None

@dataclass
class MemoryEntry:
    """Represents an entry in the RAG memory"""
    id: str
    content_type: str  # "text", "image", "json", "csv", "visio"
    content: Union[str, bytes, Dict[str, Any]]
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    timestamp: Optional[datetime] = None

class RAGMemoryService:
    """Enhanced service for managing RAG memory with multiple vector stores"""
    
    def __init__(
        self,
        store_type: VectorStoreType,
        connection_params: Dict[str, Any],
        ai_service_manager: AIServiceManager,
        embedding_dimension: int = 1536,
        similarity_threshold: float = 0.7,
        schema_dir: Optional[Path] = None
    ):
        """Initialize the RAG memory service
        
        Args:
            store_type: Type of vector store to use
            connection_params: Connection parameters for vector store
            ai_service_manager: AI service manager for embeddings
            embedding_dimension: Dimension of embeddings
            similarity_threshold: Minimum similarity score for queries
            schema_dir: Directory containing schema definitions
        """
        self.ai_service_manager = ai_service_manager
        self.embedding_dimension = embedding_dimension
        self.similarity_threshold = similarity_threshold
        self.schema_dir = schema_dir or Path("config/schemas")
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize vector store
        self.store = VectorStoreFactory.get_provider(store_type)
        self.store.initialize(
            connection_params=connection_params,
            index_name="rag_memory",
            dimension=embedding_dimension
        )
        
        # Load schemas
        self.schemas: Dict[str, DocumentSchema] = {}
        self._load_schemas()
        
        logger.info(
            f"Initialized RAG memory service with {store_type} store "
            f"and {len(self.schemas)} schemas"
        )
    
    def _load_schemas(self) -> None:
        """Load schema definitions from schema directory"""
        try:
            for schema_file in self.schema_dir.glob("*.json"):
                with open(schema_file) as f:
                    schema_data = json.load(f)
                    
                    schema = DocumentSchema(
                        fields=schema_data["fields"],
                        version=schema_data["version"],
                        description=schema_data.get("description")
                    )
                    
                    self.schemas[schema_file.stem] = schema
                    logger.info(f"Loaded schema: {schema_file.stem}")
                    
        except Exception as e:
            logger.error(f"Error loading schemas: {str(e)}")
            raise
    
    async def store_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        schema_name: Optional[str] = None
    ) -> str:
        """Store text content in memory"""
        try:
            # Clean and format text
            text = self._clean_text(text)
            
            # Generate embedding
            provider = self.ai_service_manager.get_provider()
            embedding = await provider.generate_embedding(text)
            
            # Create document
            doc = VectorDocument(
                id=self._generate_id(),
                content=text,
                metadata={
                    **(metadata or {}),
                    "content_type": "text",
                    "word_count": len(text.split())
                },
                embedding=embedding,
                timestamp=datetime.utcnow()
            )
            
            # Validate against schema if specified
            if schema_name:
                schema = self.schemas.get(schema_name)
                if not schema:
                    raise ValueError(f"Schema not found: {schema_name}")
                
                errors = await self.store.validate_schema(schema.fields, doc)
                if errors:
                    raise ValueError(f"Schema validation failed: {errors}")
            
            # Store document
            [doc_id] = await self.store.add_documents([doc])
            logger.info(f"Stored text entry with ID: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Error storing text: {str(e)}")
            raise
    
    async def store_image(
        self,
        image_data: bytes,
        metadata: Optional[Dict[str, Any]] = None,
        extract_text: bool = True,
        schema_name: Optional[str] = None
    ) -> str:
        """Store image content in memory"""
        try:
            # Extract image metadata
            image = Image.open(io.BytesIO(image_data))
            image_metadata = {
                "format": image.format,
                "width": image.width,
                "height": image.height,
                "mode": image.mode
            }
            
            # Extract text if requested
            text_content = None
            if extract_text:
                provider = self.ai_service_manager.get_provider()
                text_content = await provider.analyze_image(
                    image_data=image_data,
                    prompt="Describe this image in detail"
                )
            
            # Generate embedding from image
            provider = self.ai_service_manager.get_provider()
            if text_content:
                embedding = await provider.generate_embedding(text_content)
            else:
                # Use image embedding model
                embedding = await provider.generate_embedding(
                    image_data,
                    model="image-embed"
                )
            
            # Create document
            doc = VectorDocument(
                id=self._generate_id(),
                content=image_data,
                metadata={
                    **(metadata or {}),
                    "content_type": "image",
                    "image_metadata": image_metadata,
                    "ocr_text": text_content
                },
                embedding=embedding,
                timestamp=datetime.utcnow()
            )
            
            # Validate against schema if specified
            if schema_name:
                schema = self.schemas.get(schema_name)
                if not schema:
                    raise ValueError(f"Schema not found: {schema_name}")
                
                errors = await self.store.validate_schema(schema.fields, doc)
                if errors:
                    raise ValueError(f"Schema validation failed: {errors}")
            
            # Store document
            [doc_id] = await self.store.add_documents([doc])
            logger.info(f"Stored image entry with ID: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Error storing image: {str(e)}")
            raise
    
    async def store_structured_data(
        self,
        data: Dict[str, Any],
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        schema_name: Optional[str] = None
    ) -> str:
        """Store structured data in memory"""
        try:
            # Validate content type
            if content_type not in ["json", "csv", "visio"]:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            # Clean and format data
            cleaned_data = self._clean_structured_data(data)
            
            # Generate text representation for embedding
            text_repr = json.dumps(cleaned_data, sort_keys=True)
            
            # Generate embedding
            provider = self.ai_service_manager.get_provider()
            embedding = await provider.generate_embedding(text_repr)
            
            # Create document
            doc = VectorDocument(
                id=self._generate_id(),
                content=cleaned_data,
                metadata={
                    **(metadata or {}),
                    "content_type": content_type
                },
                embedding=embedding,
                timestamp=datetime.utcnow()
            )
            
            # Validate against schema if specified
            if schema_name:
                schema = self.schemas.get(schema_name)
                if not schema:
                    raise ValueError(f"Schema not found: {schema_name}")
                
                errors = await self.store.validate_schema(schema.fields, doc)
                if errors:
                    raise ValueError(f"Schema validation failed: {errors}")
            
            # Store document
            [doc_id] = await self.store.add_documents([doc])
            logger.info(f"Stored {content_type} entry with ID: {doc_id}")
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Error storing structured data: {str(e)}")
            raise
    
    async def query_memory(
        self,
        query: str,
        limit: int = 10,
        content_type: Optional[str] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
        use_llm_rewrite: bool = False
    ) -> List[Tuple[MemoryEntry, float]]:
        """Query memory for relevant entries"""
        try:
            # Generate query embedding
            provider = self.ai_service_manager.get_provider()
            query_embedding = await provider.generate_embedding(query)
            
            # Use LLM to generate alternative queries if requested
            if use_llm_rewrite:
                alt_queries = await self._generate_alternative_queries(query)
                alt_embeddings = [
                    await provider.generate_embedding(q)
                    for q in alt_queries
                ]
            else:
                alt_embeddings = []
            
            # Query vector store with all embeddings
            all_results = []
            
            # Query with original embedding
            results = await self.store.query(
                query_embedding=query_embedding,
                filter_metadata=metadata_filters,
                limit=limit,
                min_score=self.similarity_threshold
            )
            all_results.extend(results)
            
            # Query with alternative embeddings
            for alt_embedding in alt_embeddings:
                alt_results = await self.store.query(
                    query_embedding=alt_embedding,
                    filter_metadata=metadata_filters,
                    limit=limit,
                    min_score=self.similarity_threshold
                )
                all_results.extend(alt_results)
            
            # Deduplicate and sort results
            seen_ids = set()
            unique_results = []
            
            for result in sorted(
                all_results,
                key=lambda x: x.score,
                reverse=True
            ):
                if result.document.id not in seen_ids:
                    seen_ids.add(result.document.id)
                    
                    # Convert to MemoryEntry
                    entry = MemoryEntry(
                        id=result.document.id,
                        content_type=result.document.metadata["content_type"],
                        content=result.document.content,
                        metadata=result.document.metadata,
                        embedding=result.document.embedding,
                        timestamp=result.document.timestamp
                    )
                    
                    unique_results.append((entry, result.score))
                    
                    if len(unique_results) >= limit:
                        break
            
            logger.info(f"Found {len(unique_results)} entries matching query")
            return unique_results
            
        except Exception as e:
            logger.error(f"Error querying memory: {str(e)}")
            raise
    
    async def query_images(
        self,
        query: Union[str, bytes],
        limit: int = 10,
        metadata_filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[MemoryEntry, float]]:
        """Query memory for similar images"""
        try:
            # Generate query embedding
            provider = self.ai_service_manager.get_provider()
            
            if isinstance(query, str):
                # Text-to-image search
                query_embedding = await provider.generate_embedding(query)
            else:
                # Image-to-image search
                query_embedding = await provider.generate_embedding(
                    query,
                    model="image-embed"
                )
            
            # Add content type filter for images
            filters = {
                **(metadata_filters or {}),
                "content_type": "image"
            }
            
            # Query vector store
            results = await self.store.query(
                query_embedding=query_embedding,
                filter_metadata=filters,
                limit=limit,
                min_score=self.similarity_threshold
            )
            
            # Convert results to MemoryEntry objects
            entries = []
            for result in results:
                # Create ImageData object
                image_data = ImageData(
                    data=result.document.content,
                    format=result.document.metadata["image_metadata"]["format"],
                    width=result.document.metadata["image_metadata"]["width"],
                    height=result.document.metadata["image_metadata"]["height"],
                    ocr_text=result.document.metadata.get("ocr_text")
                )
                
                entry = MemoryEntry(
                    id=result.document.id,
                    content_type="image",
                    content=image_data,
                    metadata=result.document.metadata,
                    embedding=result.document.embedding,
                    timestamp=result.document.timestamp
                )
                
                entries.append((entry, result.score))
            
            logger.info(f"Found {len(entries)} matching images")
            return entries
            
        except Exception as e:
            logger.error(f"Error querying images: {str(e)}")
            raise
    
    async def _generate_alternative_queries(self, query: str) -> List[str]:
        """Generate alternative search queries using LLM"""
        try:
            provider = self.ai_service_manager.get_provider()
            
            prompt = f"""
            Generate 3 alternative search queries that capture different aspects
            or phrasings of the following query. Each query should focus on a
            different perspective or detail.
            
            Original query: {query}
            
            Format each alternative query on a new line starting with a hyphen.
            """
            
            response = await provider.generate_text(prompt)
            
            # Parse response
            alt_queries = [
                line.strip("- ").strip()
                for line in response.strip().split("\n")
                if line.strip().startswith("-")
            ]
            
            logger.info(
                f"Generated {len(alt_queries)} alternative queries for: {query}"
            )
            return alt_queries
            
        except Exception as e:
            logger.error(f"Error generating alternative queries: {str(e)}")
            return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and format text content"""
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Remove control characters
        text = "".join(char for char in text if char.isprintable())
        
        return text
    
    def _clean_structured_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and format structured data"""
        cleaned = {}
        
        for key, value in data.items():
            # Clean keys
            clean_key = key.strip().lower().replace(" ", "_")
            
            # Clean values recursively
            if isinstance(value, dict):
                cleaned[clean_key] = self._clean_structured_data(value)
            elif isinstance(value, list):
                cleaned[clean_key] = [
                    self._clean_structured_data(v) if isinstance(v, dict)
                    else v
                    for v in value
                ]
            elif isinstance(value, str):
                cleaned[clean_key] = self._clean_text(value)
            else:
                cleaned[clean_key] = value
        
        return cleaned
    
    def _generate_id(self) -> str:
        """Generate a unique document ID"""
        return f"doc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def delete_entry(self, entry_id: str):
        """Deletes an entry from memory"""
        try:
            self.store.delete_document(entry_id)
            logger.info(f"Deleted entry with ID: {entry_id}")
        except Exception as e:
            logger.error(f"Error deleting entry: {str(e)}")
            raise
    
    def update_metadata(
        self,
        entry_id: str,
        metadata: Dict[str, Any]
    ):
        """Updates metadata for an entry"""
        try:
            self.store.update_metadata(entry_id, metadata)
            logger.info(f"Updated metadata for entry: {entry_id}")
        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}")
            raise
    
    def get_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        """Retrieves a specific entry by ID"""
        try:
            document = self.store.get_document(entry_id)
            if not document:
                return None
                
            return MemoryEntry(
                id=document.id,
                content_type=document.metadata["content_type"],
                content=document.content,
                metadata=document.metadata,
                embedding=document.embedding,
                timestamp=document.timestamp
            )
            
        except Exception as e:
            logger.error(f"Error retrieving entry: {str(e)}")
            raise 