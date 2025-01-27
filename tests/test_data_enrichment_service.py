import pytest
from pathlib import Path
import tempfile
import aiohttp
from unittest.mock import Mock, patch
import json
from datetime import datetime

from src.services.data_enrichment_service import DataEnrichmentService
from src.services.file_cache_service import FileCacheService
from src.services.file_validator_service import FileCategory
from src.services.exceptions import ProcessingError, ValidationError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def cache_service(temp_dir):
    return FileCacheService(
        cache_dir=temp_dir / "cache",
        max_cache_size=5 * 1024 * 1024,  # 5MB
        cache_ttl=60,  # 1 minute
        cleanup_interval=5  # 5 seconds
    )

@pytest.fixture
def enrichment_service(cache_service, temp_dir):
    return DataEnrichmentService(
        cache_service=cache_service,
        download_dir=temp_dir / "downloads",
        max_download_size=1024 * 1024  # 1MB
    )

class MockResponse:
    def __init__(self, status, content, content_length=None):
        self.status = status
        self._content = content
        self.content_length = content_length
    
    @property
    def content(self):
        return self
    
    async def iter_chunked(self, chunk_size):
        yield self._content

@pytest.mark.asyncio
async def test_download_file_success(enrichment_service, temp_dir):
    url = "http://example.com/test.txt"
    content = b"Test file content"
    
    # Mock aiohttp response
    mock_response = MockResponse(200, content, len(content))
    mock_session = Mock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await enrichment_service.download_file(url)
    
    # Verify result
    assert result["url"] == url
    assert result["size"] == len(content)
    assert result["mime_type"] == "text/plain"
    assert result["category"] == FileCategory.DOCUMENT
    assert "hash" in result
    assert "downloaded_at" in result
    assert not result["from_cache"]
    
    # Verify file was cached
    cached_path = Path(result["file_path"])
    assert cached_path.exists()
    with open(cached_path, "rb") as f:
        assert f.read() == content

@pytest.mark.asyncio
async def test_download_file_from_cache(enrichment_service, temp_dir):
    url = "http://example.com/test.txt"
    content = b"Test file content"
    
    # First download to cache
    mock_response = MockResponse(200, content, len(content))
    mock_session = Mock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        result1 = await enrichment_service.download_file(url)
    
    # Second download should use cache
    result2 = await enrichment_service.download_file(url)
    
    # Verify results
    assert result2["url"] == url
    assert result2["from_cache"] is True
    assert result2["file_path"] == result1["file_path"]

@pytest.mark.asyncio
async def test_download_large_file(enrichment_service):
    url = "http://example.com/large.txt"
    content = b"0" * (2 * 1024 * 1024)  # 2MB
    
    mock_response = MockResponse(200, content, len(content))
    mock_session = Mock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(ProcessingError) as exc_info:
            await enrichment_service.download_file(url)
        assert "size exceeds limit" in str(exc_info.value)

@pytest.mark.asyncio
async def test_download_invalid_url(enrichment_service):
    url = "http://example.com/invalid"
    
    mock_response = MockResponse(404, b"Not Found")
    mock_session = Mock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        with pytest.raises(ProcessingError) as exc_info:
            await enrichment_service.download_file(url)
        assert "HTTP 404" in str(exc_info.value)

@pytest.mark.asyncio
async def test_enrich_document(enrichment_service, temp_dir):
    # Create test document
    doc_path = temp_dir / "test.txt"
    with open(doc_path, "wb") as f:
        f.write(b"Test document")
    
    # Mock file download
    url = "http://example.com/data.txt"
    content = b"Enrichment data"
    mock_response = MockResponse(200, content, len(content))
    mock_session = Mock()
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    enrichment_data = [
        {
            "url": url,
            "metadata": {"type": "reference"}
        },
        {
            "type": "metadata",
            "data": {"key": "value"}
        }
    ]
    
    with patch("aiohttp.ClientSession", return_value=mock_session):
        result = await enrichment_service.enrich_document(doc_path, enrichment_data)
    
    # Verify result
    assert result["document_path"] == str(doc_path)
    assert "enriched_at" in result
    assert len(result["results"]) == 2
    
    # Verify file download result
    file_result = result["results"][0]
    assert file_result["type"] == "file"
    assert file_result["source"] == url
    assert file_result["metadata"] == {"type": "reference"}
    
    # Verify data result
    data_result = result["results"][1]
    assert data_result["type"] == "data"
    assert data_result["data"] == {"type": "metadata", "data": {"key": "value"}} 