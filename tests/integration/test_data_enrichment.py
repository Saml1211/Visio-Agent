import pytest
import asyncio
from pathlib import Path
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.services.data_enrichment_service import DataEnrichmentService
from src.services.file_cache_service import FileCacheService
from src.services.web_search_service import WebSearchService
from src.services.ai_service_config import AIServiceManager
from src.services.exceptions import ProcessingError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def cache_service(temp_dir):
    return FileCacheService(
        cache_dir=temp_dir / "cache",
        max_cache_size=5 * 1024 * 1024,
        cache_ttl=60,
        cleanup_interval=5
    )

@pytest.fixture
def mock_web_search():
    mock = AsyncMock()
    mock.search.return_value = [
        {
            "title": "Test Result",
            "snippet": "Relevant information",
            "url": "https://test.com/info"
        }
    ]
    return mock

@pytest.fixture
def mock_ai_service():
    mock = AsyncMock()
    mock.analyze_content.return_value = {
        "summary": "Test summary",
        "key_points": ["Point 1", "Point 2"],
        "confidence": 0.95
    }
    return mock

@pytest.fixture
async def enrichment_service(cache_service, mock_web_search, mock_ai_service, temp_dir):
    service = DataEnrichmentService(
        cache_service=cache_service,
        web_search=mock_web_search,
        ai_service=mock_ai_service,
        download_dir=temp_dir / "downloads"
    )
    await service.initialize()
    return service

@pytest.mark.asyncio
async def test_full_enrichment_flow(enrichment_service):
    """Test the complete data enrichment flow"""
    input_data = {
        "component": {
            "name": "Projector X1000",
            "type": "projector"
        }
    }
    
    # Perform enrichment
    result = await enrichment_service.enrich_data(input_data)
    
    # Verify web search was called
    enrichment_service.web_search.search.assert_called_once()
    
    # Verify AI analysis was performed
    enrichment_service.ai_service.analyze_content.assert_called_once()
    
    # Verify result structure
    assert "enriched_data" in result
    assert "metadata" in result
    assert "confidence_score" in result["metadata"]
    assert result["metadata"]["confidence_score"] >= 0.9
    
    # Verify data was cached
    cache_key = enrichment_service._generate_cache_key(input_data)
    cached_data = await enrichment_service.cache_service.get_cached_data(cache_key)
    assert cached_data is not None

@pytest.mark.asyncio
async def test_enrichment_with_rate_limiting(enrichment_service):
    """Test enrichment with rate limiting"""
    # Configure mock for rate limit
    enrichment_service.web_search.search.side_effect = [
        ProcessingError("Rate limit exceeded"),
        [{"title": "Result", "snippet": "Data"}]
    ]
    
    result = await enrichment_service.enrich_data({"test": "data"})
    
    # Verify retry worked
    assert enrichment_service.web_search.search.call_count == 2
    assert result is not None

@pytest.mark.asyncio
async def test_enrichment_error_handling(enrichment_service):
    """Test error handling in enrichment flow"""
    # Configure mock to simulate error
    enrichment_service.web_search.search.side_effect = Exception("API Error")
    
    with pytest.raises(ProcessingError) as exc_info:
        await enrichment_service.enrich_data({"test": "data"})
    
    assert "Failed to enrich data" in str(exc_info.value)

@pytest.mark.asyncio
async def test_parallel_enrichment(enrichment_service):
    """Test parallel data enrichment"""
    input_data_list = [
        {"component": {"name": f"Test {i}"}}
        for i in range(5)
    ]
    
    # Perform parallel enrichment
    results = await asyncio.gather(*[
        enrichment_service.enrich_data(data)
        for data in input_data_list
    ])
    
    # Verify all requests were processed
    assert len(results) == len(input_data_list)
    assert all(r is not None for r in results)
    
    # Verify rate limiting was respected
    call_timestamps = [
        call[1]["timestamp"]
        for call in enrichment_service.web_search.search.call_args_list
    ]
    for i in range(1, len(call_timestamps)):
        time_diff = call_timestamps[i] - call_timestamps[i-1]
        assert time_diff >= enrichment_service.rate_limit_delay 