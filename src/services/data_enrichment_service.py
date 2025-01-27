import logging
from pathlib import Path
from typing import Optional, Dict, List
import aiohttp
import aiofiles
from datetime import datetime
import hashlib
import json

from .file_cache_service import FileCacheService
from .file_validator_service import FileValidator, FileCategory
from .exceptions import ProcessingError, ValidationError

logger = logging.getLogger(__name__)

class DataEnrichmentService:
    """Service for enriching documents with external data"""
    
    def __init__(
        self,
        cache_service: FileCacheService,
        download_dir: Path,
        max_download_size: int = 50 * 1024 * 1024  # 50MB
    ):
        """
        Initialize the data enrichment service
        
        Args:
            cache_service: File cache service instance
            download_dir: Directory for temporary downloads
            max_download_size: Maximum download size in bytes
        """
        self.cache_service = cache_service
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.max_download_size = max_download_size
        
        self.file_validator = FileValidator(max_file_size=max_download_size)
        
        logger.info(
            f"Initialized DataEnrichmentService with download_dir={download_dir}, "
            f"max_download_size={max_download_size}"
        )
    
    async def download_file(
        self,
        url: str,
        metadata: Optional[Dict] = None,
        allowed_categories: Optional[Set[FileCategory]] = None
    ) -> Dict:
        """
        Download and cache a file from a URL
        
        Args:
            url: URL to download from
            metadata: Optional metadata about the file
            allowed_categories: Set of allowed file categories
        
        Returns:
            Dict containing file info and path
        
        Raises:
            ProcessingError: If download or processing fails
            ValidationError: If file validation fails
        """
        try:
            logger.info(f"Starting download from URL: {url}")
            
            # Generate temp filename from URL
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            temp_path = self.download_dir / f"temp_{url_hash}"
            
            # Check cache first
            if cached_path := await self.cache_service.get_cached_file(temp_path):
                logger.info(f"Found cached file for URL: {url}")
                return {
                    "url": url,
                    "file_path": str(cached_path),
                    "from_cache": True,
                    "metadata": metadata or {}
                }
            
            # Download file
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise ProcessingError(
                            f"Failed to download file: HTTP {response.status}"
                        )
                    
                    # Check content length
                    content_length = response.content_length
                    if content_length and content_length > self.max_download_size:
                        raise ProcessingError(
                            f"File size {content_length} exceeds limit "
                            f"{self.max_download_size}"
                        )
                    
                    # Download to temp file
                    async with aiofiles.open(temp_path, "wb") as f:
                        total_size = 0
                        async for chunk in response.content.iter_chunked(8192):
                            total_size += len(chunk)
                            if total_size > self.max_download_size:
                                raise ProcessingError(
                                    f"Download size exceeds limit "
                                    f"{self.max_download_size}"
                                )
                            await f.write(chunk)
            
            # Validate downloaded file
            validation = self.file_validator.validate_file(
                temp_path,
                allowed_categories=allowed_categories
            )
            
            # Cache the file
            cached_path = await self.cache_service.cache_file(temp_path)
            if not cached_path:
                raise ProcessingError("Failed to cache downloaded file")
            
            # Clean up temp file
            temp_path.unlink()
            
            result = {
                "url": url,
                "file_path": str(cached_path),
                "size": validation["size"],
                "mime_type": validation["mime_type"],
                "category": validation["category"],
                "hash": validation["hash"],
                "from_cache": False,
                "downloaded_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            logger.info(f"Successfully downloaded and cached file from URL: {url}")
            return result
            
        except ValidationError as e:
            logger.error(f"Validation error during download: {str(e)}")
            if temp_path.exists():
                temp_path.unlink()
            raise
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            if temp_path.exists():
                temp_path.unlink()
            raise ProcessingError(f"File download failed: {str(e)}")
    
    async def enrich_document(
        self,
        document_path: Path,
        enrichment_data: List[Dict]
    ) -> Dict:
        """
        Enrich a document with downloaded data
        
        Args:
            document_path: Path to the document
            enrichment_data: List of enrichment data sources
        
        Returns:
            Dict containing enrichment results
        """
        try:
            logger.info(f"Starting document enrichment: {document_path}")
            
            results = []
            for data in enrichment_data:
                if url := data.get("url"):
                    # Download and cache file
                    download_result = await self.download_file(
                        url,
                        metadata=data.get("metadata"),
                        allowed_categories=data.get("allowed_categories")
                    )
                    results.append({
                        "type": "file",
                        "source": url,
                        **download_result
                    })
                else:
                    # Store other enrichment data
                    results.append({
                        "type": "data",
                        "data": data
                    })
            
            return {
                "document_path": str(document_path),
                "enriched_at": datetime.now().isoformat(),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error during document enrichment: {str(e)}")
            raise ProcessingError(f"Document enrichment failed: {str(e)}") 