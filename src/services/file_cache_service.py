import logging
from pathlib import Path
import shutil
from typing import Optional, Dict, Set
import json
from datetime import datetime, timedelta
import asyncio
import aiofiles
from .file_validator_service import FileValidator

logger = logging.getLogger(__name__)

class FileCacheService:
    """Service for caching frequently downloaded files"""
    
    def __init__(
        self,
        cache_dir: Path,
        max_cache_size: int = 1024 * 1024 * 1024,  # 1GB
        cache_ttl: int = 3600,  # 1 hour
        cleanup_interval: int = 300  # 5 minutes
    ):
        """
        Initialize the cache service
        
        Args:
            cache_dir: Directory for cached files
            max_cache_size: Maximum cache size in bytes
            cache_ttl: Time to live for cached files in seconds
            cleanup_interval: Interval for cache cleanup in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.max_cache_size = max_cache_size
        self.cache_ttl = cache_ttl
        self.cleanup_interval = cleanup_interval
        self.metadata_file = self.cache_dir / "metadata.json"
        self.file_validator = FileValidator()
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata
        self._init_metadata()
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_loop())
    
    def _init_metadata(self) -> None:
        """Initialize or load cache metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                "files": {},
                "total_size": 0,
                "last_cleanup": datetime.now().isoformat()
            }
            self._save_metadata()
    
    def _save_metadata(self) -> None:
        """Save cache metadata to file"""
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)
    
    async def get_cached_file(self, file_path: Path) -> Optional[Path]:
        """
        Get a file from cache if available and valid
        
        Args:
            file_path: Original file path
        
        Returns:
            Path to cached file if available, None otherwise
        """
        try:
            # Validate original file
            validation = self.file_validator.validate_file(file_path)
            file_hash = validation["hash"]
            
            # Check if file is in cache
            if file_hash in self.metadata["files"]:
                cache_info = self.metadata["files"][file_hash]
                cached_path = self.cache_dir / file_hash
                
                # Check if cache is still valid
                cache_time = datetime.fromisoformat(cache_info["cached_at"])
                if (datetime.now() - cache_time).total_seconds() < self.cache_ttl:
                    # Update access time
                    cache_info["last_accessed"] = datetime.now().isoformat()
                    cache_info["access_count"] += 1
                    self._save_metadata()
                    
                    return cached_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached file: {str(e)}")
            return None
    
    async def cache_file(self, file_path: Path) -> Optional[Path]:
        """
        Cache a file for future use
        
        Args:
            file_path: File to cache
        
        Returns:
            Path to cached file if successful, None otherwise
        """
        try:
            # Validate file
            validation = self.file_validator.validate_file(file_path)
            file_hash = validation["hash"]
            file_size = validation["size"]
            
            # Check if we need to make space
            if self.metadata["total_size"] + file_size > self.max_cache_size:
                await self._make_space(file_size)
            
            # Copy file to cache
            cached_path = self.cache_dir / file_hash
            await self._copy_file(file_path, cached_path)
            
            # Update metadata
            self.metadata["files"][file_hash] = {
                "original_path": str(file_path),
                "size": file_size,
                "mime_type": validation["mime_type"],
                "cached_at": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "access_count": 1
            }
            self.metadata["total_size"] += file_size
            self._save_metadata()
            
            return cached_path
            
        except Exception as e:
            logger.error(f"Error caching file: {str(e)}")
            return None
    
    async def _copy_file(self, src: Path, dst: Path) -> None:
        """Copy file using async IO"""
        async with aiofiles.open(src, "rb") as fsrc:
            async with aiofiles.open(dst, "wb") as fdst:
                chunk = await fsrc.read(8192)
                while chunk:
                    await fdst.write(chunk)
                    chunk = await fsrc.read(8192)
    
    async def _make_space(self, needed_size: int) -> None:
        """
        Make space in cache for new file
        
        Args:
            needed_size: Size needed in bytes
        """
        # Sort files by last access time and access count
        sorted_files = sorted(
            self.metadata["files"].items(),
            key=lambda x: (
                datetime.fromisoformat(x[1]["last_accessed"]),
                x[1]["access_count"]
            )
        )
        
        # Remove files until we have enough space
        for file_hash, info in sorted_files:
            if self.metadata["total_size"] + needed_size <= self.max_cache_size:
                break
                
            cached_path = self.cache_dir / file_hash
            try:
                cached_path.unlink()
                self.metadata["total_size"] -= info["size"]
                del self.metadata["files"][file_hash]
            except Exception as e:
                logger.error(f"Error removing cached file: {str(e)}")
    
    async def _cleanup_loop(self) -> None:
        """Background task for cache cleanup"""
        while True:
            try:
                # Remove expired files
                now = datetime.now()
                expired_hashes = [
                    h for h, info in self.metadata["files"].items()
                    if (now - datetime.fromisoformat(info["cached_at"])).total_seconds() > self.cache_ttl
                ]
                
                for file_hash in expired_hashes:
                    cached_path = self.cache_dir / file_hash
                    info = self.metadata["files"][file_hash]
                    try:
                        cached_path.unlink()
                        self.metadata["total_size"] -= info["size"]
                        del self.metadata["files"][file_hash]
                    except Exception as e:
                        logger.error(f"Error cleaning up cached file: {str(e)}")
                
                self.metadata["last_cleanup"] = now.isoformat()
                self._save_metadata()
                
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")
            
            await asyncio.sleep(self.cleanup_interval) 