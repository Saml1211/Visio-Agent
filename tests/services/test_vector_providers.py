import pytest
from src.services.vector_store import VectorStoreFactory
from src.models.rag_models import VectorDocument

@pytest.mark.asyncio
async def test_pinecone_integration():
    provider = VectorStoreFactory.create_provider("pinecone")
    await provider.connect({
        "api_key": "test-key",
        "environment": "test-env",
        "index_name": "test-index"
    })
    
    test_doc = VectorDocument(
        id="test1",
        content="Test content",
        metadata={"type": "test"},
        embedding=[0.1]*768
    )
    
    doc_ids = await provider.add_documents([test_doc])
    assert len(doc_ids) == 1
    assert doc_ids[0].startswith("doc_test1") 