import pytest
from unittest.mock import AsyncMock
from src.services.processing.batch_processor import BatchProcessor

@pytest.mark.asyncio
async def test_batch_processing():
    mock_store = AsyncMock()
    mock_store.add_documents.return_value = ["doc1", "doc2"]
    
    processor = BatchProcessor(mock_store, schema=MockSchema())
    docs = [valid_doc1, valid_doc2]
    
    result = await processor.process_batch(docs)
    assert result["success"] == 2
    assert len(result["errors"]) == 0 