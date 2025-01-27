from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from .exceptions import ProcessingError
from .rag_memory_service import RAGMemoryService
from .data_ingestion import JinaReaderService, FirecrawlService

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Service for processing input documents for LLD generation"""
    
    def __init__(self, rag_memory: RAGMemoryService, jina_reader: JinaReaderService, firecrawl: FirecrawlService):
        """Initialize the document processing service
        
        Args:
            rag_memory: RAG memory service for storing processed content
            jina_reader: Jina Reader service for reading URLs
            firecrawl: Firecrawl service for scraping URLs
        """
        self.rag_memory = rag_memory
        self.jina_reader = jina_reader
        self.firecrawl = firecrawl
        
    async def process_document(
        self,
        file_path: Path,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process an input document for LLD generation
        
        Args:
            file_path: Path to the document file
            context: Optional processing context
            
        Returns:
            Dict containing processed content and metadata
        """
        try:
            # Handle URL inputs
            if str(file_path).startswith(('http://', 'https://')):
                return await self._process_url(file_path)
            
            # Validate file type
            allowed_types = {'.txt', '.md', '.json', '.pdf'}
            if file_path.suffix.lower() not in allowed_types:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
            # Validate file size
            max_size = 50 * 1024 * 1024  # 50MB
            if file_path.stat().st_size > max_size:
                raise ValueError("File size exceeds 50MB limit")
            
            # Check cache first
            cache_key = f"doc_process_{file_path.name}_{file_path.stat().st_mtime}"
            if cached := await self.rag_memory.query_memory(cache_key):
                logger.info(f"Found cached processing results for {file_path}")
                return cached[0].content
            
            # Process based on file type
            file_type = file_path.suffix.lower()
            if file_type == '.txt':
                processed = await self._process_text(file_path)
            elif file_type == '.md':
                processed = await self._process_markdown(file_path)
            elif file_type == '.json':
                processed = await self._process_json(file_path)
            else:
                raise ProcessingError(f"Unsupported file type: {file_type}")
                
            # Store in memory
            await self.rag_memory.store_entry(
                content=processed,
                metadata={
                    'file_name': file_path.name,
                    'file_type': file_type,
                    'cache_key': cache_key
                }
            )
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
            raise ProcessingError(f"Document processing failed: {str(e)}")
            
    async def _process_text(self, file_path: Path) -> Dict[str, Any]:
        """Process a text file"""
        try:
            with open(file_path) as f:
                content = f.read()
                
            return {
                'content': content,
                'format': 'text'
            }
            
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            raise ProcessingError(f"Text processing failed: {str(e)}")
            
    async def _process_markdown(self, file_path: Path) -> Dict[str, Any]:
        """Process a markdown file"""
        try:
            with open(file_path) as f:
                content = f.read()
                
            return {
                'content': content,
                'format': 'markdown'
            }
            
        except Exception as e:
            logger.error(f"Error processing markdown file {file_path}: {str(e)}")
            raise ProcessingError(f"Markdown processing failed: {str(e)}")
            
    async def _process_json(self, file_path: Path) -> Dict[str, Any]:
        """Process a JSON file"""
        try:
            with open(file_path) as f:
                content = f.read()
                
            return {
                'content': content,
                'format': 'json'
            }
            
        except Exception as e:
            logger.error(f"Error processing JSON file {file_path}: {str(e)}")
            raise ProcessingError(f"JSON processing failed: {str(e)}")
            
    async def _process_url(self, url: str) -> Dict:
        """Process web content using optimal scraping strategy"""
        if 'specs' in url or 'technical' in url:
            return await self.firecrawl.scrape_url(url)
        return await self.jina_reader.read_url(url) 