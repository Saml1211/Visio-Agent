import pytest
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime

from src.services.document_ingestion_service import DocumentIngestionService
from src.services.file_validator_service import FileCategory
from src.services.exceptions import ValidationError, ProcessingError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def upload_dir(temp_dir):
    upload_dir = temp_dir / "uploads"
    upload_dir.mkdir()
    return upload_dir

@pytest.fixture
def ingestion_service(upload_dir):
    return DocumentIngestionService(
        upload_dir=upload_dir,
        max_file_size=1024 * 1024,  # 1MB
        allowed_categories={FileCategory.DOCUMENT}
    )

def create_test_file(path: Path, content: bytes) -> None:
    """Create a test file with specific content"""
    with open(path, "wb") as f:
        f.write(content)

@pytest.mark.asyncio
async def test_ingest_valid_document(ingestion_service, temp_dir):
    # Create test document
    doc_path = temp_dir / "test.txt"
    content = b"Test document content"
    create_test_file(doc_path, content)
    
    # Test ingestion
    result = await ingestion_service.ingest_document(doc_path)
    
    # Verify result
    assert result["original_path"] == str(doc_path)
    assert result["size"] == len(content)
    assert result["mime_type"] == "text/plain"
    assert result["category"] == FileCategory.DOCUMENT
    assert "hash" in result
    assert "uploaded_at" in result
    
    # Verify file was copied
    stored_path = Path(result["stored_path"])
    assert stored_path.exists()
    with open(stored_path, "rb") as f:
        assert f.read() == content

@pytest.mark.asyncio
async def test_ingest_with_metadata(ingestion_service, temp_dir):
    # Create test document
    doc_path = temp_dir / "test.txt"
    create_test_file(doc_path, b"Test content")
    
    # Test ingestion with metadata
    metadata = {"author": "Test User", "version": "1.0"}
    result = await ingestion_service.ingest_document(doc_path, metadata=metadata)
    
    # Verify metadata
    assert result["metadata"] == metadata

@pytest.mark.asyncio
async def test_ingest_large_file(ingestion_service, temp_dir):
    # Create large test file
    doc_path = temp_dir / "large.txt"
    create_test_file(doc_path, b"0" * (2 * 1024 * 1024))  # 2MB
    
    # Test ingestion
    with pytest.raises(ValidationError) as exc_info:
        await ingestion_service.ingest_document(doc_path)
    assert "File size exceeds limit" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ingest_invalid_category(ingestion_service, temp_dir):
    # Create test image
    img_path = temp_dir / "test.jpg"
    create_test_file(img_path, b"Fake JPEG content")
    
    # Test ingestion
    with pytest.raises(ValidationError) as exc_info:
        await ingestion_service.ingest_document(img_path)
    assert "not allowed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ingest_nonexistent_file(ingestion_service, temp_dir):
    # Test ingestion of nonexistent file
    with pytest.raises(ValidationError) as exc_info:
        await ingestion_service.ingest_document(temp_dir / "nonexistent.txt")
    assert "does not exist" in str(exc_info.value)

@pytest.mark.asyncio
async def test_unique_filenames(ingestion_service, temp_dir):
    # Create test document
    doc_path = temp_dir / "test.txt"
    create_test_file(doc_path, b"Test content")
    
    # Ingest same file twice
    result1 = await ingestion_service.ingest_document(doc_path)
    result2 = await ingestion_service.ingest_document(doc_path)
    
    # Verify unique filenames
    assert result1["file_name"] != result2["file_name"]
    assert Path(result1["stored_path"]).exists()
    assert Path(result2["stored_path"]).exists() 