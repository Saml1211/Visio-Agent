from enum import Enum
from pathlib import Path
import magic
import logging
from typing import Set, Optional, Dict, List
import mimetypes
import hashlib
from datetime import datetime, timedelta
import os
import re
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class FileCategory(str, Enum):
    """Categories of supported files"""
    DOCUMENT = "document"
    DIAGRAM = "diagram"
    IMAGE = "image"

class FileValidationResult(BaseModel):
    """Validation result with comprehensive metadata"""
    is_valid: bool = Field(..., description="Whether the file is valid")
    category: Optional[FileCategory] = Field(None, description="File category if valid")
    mime_type: Optional[str] = Field(None, description="Detected MIME type")
    size: int = Field(..., description="File size in bytes")
    hash: str = Field(..., description="SHA-256 hash of file")
    validation_time: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    
    @validator("mime_type")
    def validate_mime_type(cls, v, values):
        if values.get("is_valid") and not v:
            raise ValueError("MIME type must be provided for valid files")
        return v
    
    @validator("size")
    def validate_size(cls, v):
        if v < 0:
            raise ValueError("File size cannot be negative")
        return v
    
    @validator("hash")
    def validate_hash(cls, v):
        if not re.match(r"^[a-fA-F0-9]{64}$", v):
            raise ValueError("Invalid SHA-256 hash format")
        return v

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
    
    def __init__(
        self,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB default
        allowed_extensions: Optional[Set[str]] = None
    ):
        """Initialize the validator
        
        Args:
            max_file_size: Maximum allowed file size in bytes
            allowed_extensions: Optional set of allowed file extensions
        """
        if max_file_size <= 0:
            raise ValueError("max_file_size must be positive")
            
        self.max_file_size = max_file_size
        self.allowed_extensions = allowed_extensions
        self.mime = magic.Magic(mime=True)
    
    def validate_file(
        self,
        file_path: Path,
        allowed_categories: Optional[Set[FileCategory]] = None
    ) -> FileValidationResult:
        """Validate a file against security and type constraints
        
        Args:
            file_path: Path to file to validate
            allowed_categories: Optional set of allowed categories
            
        Returns:
            Validation result with metadata
            
        Raises:
            ValueError: If file is invalid
        """
        errors = []
        
        # Basic path validation
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
            
        if not file_path.exists():
            errors.append("File does not exist")
            return FileValidationResult(
                is_valid=False,
                size=0,
                hash="0" * 64,
                errors=errors
            )
            
        if not file_path.is_file():
            errors.append("Path is not a regular file")
            return FileValidationResult(
                is_valid=False,
                size=0,
                hash="0" * 64,
                errors=errors
            )
        
        # Size validation
        try:
            size = file_path.stat().st_size
            if size > self.max_file_size:
                errors.append(f"File size exceeds limit of {self.max_file_size} bytes")
        except OSError as e:
            errors.append(f"Error checking file size: {str(e)}")
            size = 0
        
        # Extension validation
        if self.allowed_extensions:
            if file_path.suffix.lower() not in self.allowed_extensions:
                errors.append("File extension not allowed")
        
        # Calculate file hash
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            errors.append(f"Error calculating file hash: {str(e)}")
            file_hash = "0" * 64
        
        # MIME type detection
        try:
            mime_type = self.mime.from_file(str(file_path))
        except Exception as e:
            errors.append(f"Error detecting MIME type: {str(e)}")
            mime_type = None
        
        # Category validation
        category = None
        if mime_type:
            for cat, allowed_types in self.ALLOWED_TYPES.items():
                if mime_type in allowed_types:
                    category = cat
                    break
            
            if category is None:
                errors.append(f"Unsupported MIME type: {mime_type}")
            elif allowed_categories and category not in allowed_categories:
                errors.append(f"File category {category} not allowed")
        
        # Create validation result
        return FileValidationResult(
            is_valid=len(errors) == 0,
            category=category,
            mime_type=mime_type,
            size=size,
            hash=file_hash,
            errors=errors
        )
    
    def get_safe_filename(self, filename: str) -> str:
        """Generate a safe version of a filename
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove potentially dangerous characters
        safe_chars = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
        
        # Ensure filename isn't empty
        if not safe_chars:
            return "unnamed_file"
            
        return safe_chars
    
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