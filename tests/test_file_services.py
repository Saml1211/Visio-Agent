import pytest
from pathlib import Path
import tempfile
import shutil
import os
import asyncio
from datetime import datetime, timedelta
import magic
import json

from src.services.file_validator_service import FileValidator, FileCategory
from src.services.file_cache_service import FileCacheService

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def validator():
    return FileValidator(max_file_size=1024 * 1024)  # 1MB

@pytest.fixture
def cache_service(temp_dir):
    return FileCacheService(
        cache_dir=temp_dir / "cache",
        max_cache_size=5 * 1024 * 1024,  # 5MB
        cache_ttl=60,  # 1 minute
        cleanup_interval=5  # 5 seconds
    )

def create_test_file(path: Path, content: bytes) -> None:
    """Create a test file with specific content"""
    with open(path, "wb") as f:
        f.write(content)

# File Validator Tests
def test_validate_valid_text_file(validator, temp_dir):
    file_path = temp_dir / "test.txt"
    create_test_file(file_path, b"Test content")
    
    result = validator.validate_file(file_path)
    assert result["is_valid"]
    assert result["category"] == FileCategory.DOCUMENT
    assert result["mime_type"] == "text/plain"

def test_validate_large_file(validator, temp_dir):
    file_path = temp_dir / "large.txt"
    create_test_file(file_path, b"0" * (2 * 1024 * 1024))  # 2MB
    
    with pytest.raises(ValueError) as exc_info:
        validator.validate_file(file_path)
    assert "File size exceeds limit" in str(exc_info.value)

def test_validate_unsupported_file(validator, temp_dir):
    file_path = temp_dir / "test.xyz"
    create_test_file(file_path, b"Invalid content")
    
    with pytest.raises(ValueError) as exc_info:
        validator.validate_file(file_path)
    assert "Unsupported file type" in str(exc_info.value)

def test_validate_with_allowed_categories(validator, temp_dir):
    file_path = temp_dir / "test.txt"
    create_test_file(file_path, b"Test content")
    
    # Test with allowed category
    result = validator.validate_file(
        file_path,
        allowed_categories={FileCategory.DOCUMENT}
    )
    assert result["is_valid"]
    
    # Test with disallowed category
    with pytest.raises(ValueError) as exc_info:
        validator.validate_file(
            file_path,
            allowed_categories={FileCategory.IMAGE}
        )
    assert "not allowed" in str(exc_info.value)

# File Cache Tests
@pytest.mark.asyncio
async def test_cache_and_retrieve_file(cache_service, temp_dir):
    # Create test file
    file_path = temp_dir / "test.txt"
    content = b"Test content"
    create_test_file(file_path, content)
    
    # Cache file
    cached_path = await cache_service.cache_file(file_path)
    assert cached_path is not None
    assert cached_path.exists()
    
    # Retrieve from cache
    retrieved_path = await cache_service.get_cached_file(file_path)
    assert retrieved_path is not None
    assert retrieved_path.exists()
    
    # Verify content
    with open(retrieved_path, "rb") as f:
        assert f.read() == content

@pytest.mark.asyncio
async def test_cache_expiration(cache_service, temp_dir):
    # Create test file
    file_path = temp_dir / "test.txt"
    create_test_file(file_path, b"Test content")
    
    # Cache file
    cached_path = await cache_service.cache_file(file_path)
    assert cached_path is not None
    
    # Wait for cache to expire
    await asyncio.sleep(cache_service.cache_ttl + 1)
    
    # Try to retrieve expired file
    retrieved_path = await cache_service.get_cached_file(file_path)
    assert retrieved_path is None

@pytest.mark.asyncio
async def test_cache_size_limit(cache_service, temp_dir):
    # Create large test files
    files = []
    for i in range(3):
        file_path = temp_dir / f"test{i}.txt"
        create_test_file(file_path, b"0" * (2 * 1024 * 1024))  # 2MB each
        files.append(file_path)
    
    # Cache files (should exceed cache size)
    for file_path in files:
        cached_path = await cache_service.cache_file(file_path)
        assert cached_path is not None
    
    # Verify oldest file was removed
    retrieved_path = await cache_service.get_cached_file(files[0])
    assert retrieved_path is None

@pytest.mark.asyncio
async def test_cache_metadata_persistence(cache_service, temp_dir):
    # Create test file
    file_path = temp_dir / "test.txt"
    create_test_file(file_path, b"Test content")
    
    # Cache file
    await cache_service.cache_file(file_path)
    
    # Verify metadata file exists and is valid JSON
    metadata_path = cache_service.metadata_file
    assert metadata_path.exists()
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
        assert "files" in metadata
        assert "total_size" in metadata
        assert metadata["total_size"] > 0

@pytest.mark.asyncio
async def test_cache_cleanup(cache_service, temp_dir):
    # Create test files
    files = []
    for i in range(2):
        file_path = temp_dir / f"test{i}.txt"
        create_test_file(file_path, b"Test content")
        files.append(file_path)
    
    # Cache files
    for file_path in files:
        await cache_service.cache_file(file_path)
    
    # Wait for cleanup
    await asyncio.sleep(cache_service.cleanup_interval + 1)
    
    # Verify cache directory is empty
    cache_files = list(cache_service.cache_dir.glob("*"))
    assert len(cache_files) <= 1  # Only metadata file should remain 