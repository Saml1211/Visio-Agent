from enum import Enum
from pathlib import Path
import magic
import logging
from typing import Set, Optional, Dict
import mimetypes
import hashlib
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileCategory(str, Enum):
    """Categories of supported files"""
    DOCUMENT = "document"
    DIAGRAM = "diagram"
    IMAGE = "image"

class FileValidator:
    """Service for validating and handling file types"""
    
    # Mapping of file categories to allowed MIME types
    ALLOWED_TYPES: Dict[FileCategory, Set[str]] = {
        FileCategory.DOCUMENT: {
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/csv'
        },
        FileCategory.DIAGRAM: {
            'application/vnd.visio',
            'application/vnd.ms-visio.drawing',
            'application/vnd.ms-visio.template'
        },
        FileCategory.IMAGE: {
            'image/jpeg',
            'image/png',
            'image/tiff'
        }
    }
    
    def __init__(self, max_file_size: int = 10 * 1024 * 1024):
        """Initialize the validator with maximum file size (default 10MB)"""
        self.max_file_size = max_file_size
        self.mime = magic.Magic(mime=True)
    
    def validate_file(
        self,
        file_path: Path,
        allowed_categories: Optional[Set[FileCategory]] = None
    ) -> Dict[str, any]:
        """
        Validate a file's type, size, and content
        
        Args:
            file_path: Path to the file
            allowed_categories: Set of allowed file categories (optional)
        
        Returns:
            Dict containing validation results
        
        Raises:
            ValueError: If file is invalid
        """
        try:
            if not file_path.exists():
                raise ValueError("File does not exist")
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise ValueError(f"File size exceeds limit of {self.max_file_size} bytes")
            
            # Get MIME type
            mime_type = self.mime.from_file(str(file_path))
            
            # Determine file category
            category = self._get_file_category(mime_type)
            if category is None:
                raise ValueError(f"Unsupported file type: {mime_type}")
            
            # Check against allowed categories
            if allowed_categories and category not in allowed_categories:
                raise ValueError(f"File category {category} not allowed")
            
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            return {
                "size": file_size,
                "mime_type": mime_type,
                "category": category,
                "hash": file_hash,
                "is_valid": True
            }
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            raise ValueError(f"File validation failed: {str(e)}")
    
    def _get_file_category(self, mime_type: str) -> Optional[FileCategory]:
        """Determine file category from MIME type"""
        for category, mime_types in self.ALLOWED_TYPES.items():
            if mime_type in mime_types:
                return category
        return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def get_extension(mime_type: str) -> str:
        """Get file extension from MIME type"""
        extension = mimetypes.guess_extension(mime_type)
        if extension is None:
            raise ValueError(f"Unknown MIME type: {mime_type}")
        return extension 