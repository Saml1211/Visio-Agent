import pytest
from src.services.vector_store.jina_provider import JinaVectorStore
from src.models import AVComponent

@pytest.fixture
def jina_store():
    return JinaVectorStore(endpoint="mock://localhost:8080")

@pytest.mark.asyncio
async def test_index_components(jina_store, mocker):
    mock_client = mocker.patch.object(jina_store, 'client')
    components = [
        AVComponent(
            id="test1",
            type="Display",
            manufacturer="Samsung",
            description="4K Display"
        )
    ]
    
    await jina_store.index_components(components)
    mock_client.post.assert_called_once()
    
@pytest.mark.asyncio
async def test_search_similar(jina_store, mocker):
    mock_client = mocker.patch.object(jina_store, 'client')
    mock_client.post.return_value = [
        mocker.Mock(
            matches=[
                mocker.Mock(
                    tags={'id': 'test2', 'type': 'Display'},
                    scores={'cosine': mocker.Mock(value=0.95)}
                )
            ]
        )
    ]
    
    query = AVComponent(
        id="test1",
        type="Display",
        manufacturer="LG",
        description="4K Display"
    )
    
    results = await jina_store.search_similar(query)
    assert len(results) == 1
    assert results[0]['id'] == 'test2'
    assert results[0]['score'] == 0.95 