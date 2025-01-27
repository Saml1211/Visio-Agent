import pytest
from src.services.data_ingestion.firecrawl_crawler import SpecCrawler
import json

@pytest.fixture
def crawler():
    return SpecCrawler(
        api_key="test-key",
        redis_url="redis://localhost:6379"
    )

@pytest.mark.asyncio
async def test_get_component_specs(crawler, mocker):
    # Mock Redis
    mock_redis = mocker.patch.object(crawler, 'redis')
    mock_redis.get.return_value = None
    
    # Mock Firecrawl client
    mock_client = mocker.patch.object(crawler, 'client')
    mock_specs = {
        'model': 'TEST-123',
        'specifications': {'resolution': '4K'}
    }
    mock_client.crawl_product_specs.return_value = mock_specs
    
    result = await crawler.get_component_specs('TestMfg', 'TEST-123')
    
    assert result == mock_specs
    mock_redis.setex.assert_called_once_with(
        'specs:TestMfg:TEST-123',
        86400,
        json.dumps(mock_specs)
    )

@pytest.mark.asyncio
async def test_cache_hit(crawler, mocker):
    mock_redis = mocker.patch.object(crawler, 'redis')
    cached_specs = {'cached': True}
    mock_redis.get.return_value = json.dumps(cached_specs)
    
    result = await crawler.get_component_specs('TestMfg', 'TEST-123')
    
    assert result == cached_specs
    mock_redis.setex.assert_not_called() 