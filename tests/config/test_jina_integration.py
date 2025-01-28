from unittest.mock import patch
from config.jina_settings import JINA_API_URL, JINA_RATE_LIMIT
from src.services.document_processing import JinaProcessor

def test_jina_connection_pooling():
    with patch('jina.Client') as mock_client:
        processor = JinaProcessor()
        processor.process("test content")
        
        # Verify connection pool settings
        _, kwargs = mock_client.call_args
        assert kwargs["max_retries"] == 3
        assert kwargs["timeout"] == 30

def test_rate_limiting():
    processor = JinaProcessor()
    assert processor.rate_limit == "100/60s"
    assert processor._client.headers["X-RateLimit-Limit"] == "100" 