import logging
from pathlib import Path
from typing import Optional, Set, Dict
import aiofiles
import hashlib
from datetime import datetime

from .file_validator_service import FileValidator, FileCategory
from .exceptions import ValidationError, ProcessingError

logger = logging.getLogger(__name__)

class DocumentIngestionService:
    """Service for ingesting and validating documents"""
    
    def __init__(
        self,
        upload_dir: Path,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_categories: Optional[Set[FileCategory]] = None
    ):
        """
        Initialize the document ingestion service
        
        Args:
            upload_dir: Directory for storing uploaded files
            max_file_size: Maximum allowed file size in bytes
            allowed_categories: Set of allowed file categories
        """
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        self.file_validator = FileValidator(max_file_size=max_file_size)
        self.allowed_categories = allowed_categories or {
            FileCategory.DOCUMENT,
            FileCategory.DIAGRAM
        }
        
        logger.info(
            f"Initialized DocumentIngestionService with upload_dir={upload_dir}, "
            f"max_file_size={max_file_size}, allowed_categories={allowed_categories}"
        )
    
    async def ingest_document(
        self,
        file_path: Path,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Ingest and validate a document
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata about the document
        
        Returns:
            Dict containing document info and validation results
        
        Raises:
            ValidationError: If document fails validation
            ProcessingError: If error occurs during processing
        """
        try:
            logger.info(f"Starting ingestion of document: {file_path}")
            
            # Validate file
            validation = self.file_validator.validate_file(
                file_path,
                allowed_categories=self.allowed_categories
            )
            
            # Generate unique filename
            unique_name = self._generate_unique_name(file_path, validation["hash"])
            dest_path = self.upload_dir / unique_name
            
            # Copy file to upload directory
            await self._copy_file(file_path, dest_path)
            
            # Prepare result
            result = {
                "original_path": str(file_path),
                "stored_path": str(dest_path),
                "file_name": unique_name,
                "size": validation["size"],
                "mime_type": validation["mime_type"],
                "category": validation["category"],
                "hash": validation["hash"],
                "uploaded_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            logger.info(f"Successfully ingested document: {result['file_name']}")
            return result
            
        except ValidationError as e:
            logger.error(f"Validation error during ingestion: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error during document ingestion: {str(e)}")
            raise ProcessingError(f"Document ingestion failed: {str(e)}")
    
    async def _copy_file(self, src: Path, dst: Path) -> None:
        """Copy file using async IO"""
        try:
            async with aiofiles.open(src, "rb") as fsrc:
                async with aiofiles.open(dst, "wb") as fdst:
                    chunk = await fsrc.read(8192)
                    while chunk:
                        await fdst.write(chunk)
                        chunk = await fsrc.read(8192)
        except Exception as e:
            logger.error(f"Error copying file: {str(e)}")
            raise ProcessingError(f"Failed to copy file: {str(e)}")
    
    def _generate_unique_name(self, original_path: Path, file_hash: str) -> str:
        """Generate unique filename using timestamp and hash"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = original_path.suffix
        return f"{timestamp}_{file_hash[:8]}{extension}" 