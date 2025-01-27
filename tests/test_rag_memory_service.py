import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
import json
import numpy as np
import io
from PIL import Image
from pathlib import Path
import base64

from src.services.rag_memory_service import (
    RAGMemoryService,
    MemoryEntry,
    DocumentSchema,
    ImageData
)
from src.services.ai_service_config import (
    AIServiceManager,
    AIServiceProvider
)
from src.services.vector_store import (
    VectorStoreType,
    VectorDocument,
    QueryResult,
    VectorStoreError
)

@pytest.fixture
def mock_vector_store():
    store = MagicMock()
    store.initialize = AsyncMock()
    store.add_documents = AsyncMock(return_value=["test_id"])
    store.query = AsyncMock(return_value=[
        QueryResult(
            document=VectorDocument(
                id="test_id",
                content="Test content",
                metadata={
                    "content_type": "text",
                    "word_count": 2
                },
                embedding=[0.1, 0.2, 0.3],
                timestamp=datetime.utcnow()
            ),
            score=0.95
        )
    ])
    store.delete_documents = AsyncMock()
    store.update_metadata = AsyncMock()
    store.get_document = AsyncMock()
    store.validate_schema = AsyncMock(return_value=[])
    return store

@pytest.fixture
def mock_ai_provider():
    provider = MagicMock()
    provider.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
    provider.analyze_image = AsyncMock(return_value="Image description")
    provider.generate_text = AsyncMock(return_value="""
    - Alternative query 1
    - Alternative query 2
    - Alternative query 3
    """)
    return provider

@pytest.fixture
def mock_ai_service_manager(mock_ai_provider):
    manager = MagicMock(spec=AIServiceManager)
    manager.get_provider.return_value = mock_ai_provider
    return manager

@pytest.fixture
def test_schema():
    return DocumentSchema(
        fields={
            "category": {
                "type": "string",
                "required": True,
                "enum": ["document", "image", "diagram"]
            },
            "tags": {
                "type": "array",
                "required": False
            },
            "version": {
                "type": "string",
                "required": True,
                "pattern": r"^\d+\.\d+\.\d+$"
            }
        },
        version="1.0.0",
        description="Test schema"
    )

@pytest.fixture
def rag_service(tmp_path, mock_vector_store, mock_ai_service_manager):
    # Create schema directory and add test schema
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()
    
    with open(schema_dir / "test.json", "w") as f:
        json.dump({
            "fields": {
                "category": {
                    "type": "string",
                    "required": True,
                    "enum": ["document", "image", "diagram"]
                },
                "tags": {
                    "type": "array",
                    "required": False
                },
                "version": {
                    "type": "string",
                    "required": True,
                    "pattern": r"^\d+\.\d+\.\d+$"
                }
            },
            "version": "1.0.0",
            "description": "Test schema"
        }, f)
    
    with patch("src.services.vector_store.factory.VectorStoreFactory.get_provider") as mock_factory:
        mock_factory.return_value = mock_vector_store
        
        service = RAGMemoryService(
            store_type=VectorStoreType.CHROMA,
            connection_params={"persist_dir": str(tmp_path / "vector_store")},
            ai_service_manager=mock_ai_service_manager,
            schema_dir=schema_dir
        )
        
        return service

@pytest.mark.asyncio
async def test_store_text(rag_service, mock_vector_store, mock_ai_provider):
    # Test data
    text = "Test content"
    metadata = {
        "category": "document",
        "version": "1.0.0"
    }
    
    # Store text with schema validation
    doc_id = await rag_service.store_text(
        text=text,
        metadata=metadata,
        schema_name="test"
    )
    
    # Verify operations
    mock_ai_provider.generate_embedding.assert_called_once_with(text)
    mock_vector_store.validate_schema.assert_called_once()
    mock_vector_store.add_documents.assert_called_once()
    assert doc_id == "test_id"

@pytest.mark.asyncio
async def test_store_text_schema_validation_failure(rag_service, mock_vector_store):
    # Test data with invalid metadata
    text = "Test content"
    metadata = {
        "category": "invalid",  # Not in enum
        "version": "1.0"  # Doesn't match pattern
    }
    
    # Configure mock to return validation errors
    mock_vector_store.validate_schema.return_value = [
        "Invalid value for category. Must be one of: ['document', 'image', 'diagram']",
        "Field version does not match pattern: ^\\d+\\.\\d+\\.\\d+$"
    ]
    
    # Test validation failure
    with pytest.raises(ValueError) as exc_info:
        await rag_service.store_text(
            text=text,
            metadata=metadata,
            schema_name="test"
        )
    
    assert "Schema validation failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_store_image(rag_service, mock_vector_store, mock_ai_provider):
    # Create test image
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    # Test data
    metadata = {
        "category": "image",
        "version": "1.0.0"
    }
    
    # Store image
    doc_id = await rag_service.store_image(
        image_data=img_bytes,
        metadata=metadata,
        schema_name="test"
    )
    
    # Verify operations
    mock_ai_provider.analyze_image.assert_called_once()
    mock_ai_provider.generate_embedding.assert_called_once()
    mock_vector_store.validate_schema.assert_called_once()
    mock_vector_store.add_documents.assert_called_once()
    assert doc_id == "test_id"

@pytest.mark.asyncio
async def test_store_structured_data(rag_service, mock_vector_store, mock_ai_provider):
    # Test data
    data = {
        "name": "Test Component",
        "properties": {
            "width": 100,
            "height": 50
        }
    }
    metadata = {
        "category": "diagram",
        "version": "1.0.0"
    }
    
    # Store structured data
    doc_id = await rag_service.store_structured_data(
        data=data,
        content_type="visio",
        metadata=metadata,
        schema_name="test"
    )
    
    # Verify operations
    mock_ai_provider.generate_embedding.assert_called_once()
    mock_vector_store.validate_schema.assert_called_once()
    mock_vector_store.add_documents.assert_called_once()
    assert doc_id == "test_id"

@pytest.mark.asyncio
async def test_query_memory_with_llm_rewrite(
    rag_service,
    mock_vector_store,
    mock_ai_provider
):
    # Test data
    query = "test query"
    metadata_filters = {"category": "document"}
    
    # Query memory with LLM rewrite
    results = await rag_service.query_memory(
        query=query,
        metadata_filters=metadata_filters,
        use_llm_rewrite=True
    )
    
    # Verify operations
    assert mock_ai_provider.generate_embedding.call_count == 4  # Original + 3 alternatives
    assert mock_ai_provider.generate_text.call_count == 1
    assert mock_vector_store.query.call_count == 4
    assert len(results) == 1
    assert isinstance(results[0][0], MemoryEntry)
    assert isinstance(results[0][1], float)

@pytest.mark.asyncio
async def test_query_images_text_to_image(
    rag_service,
    mock_vector_store,
    mock_ai_provider
):
    # Configure mock for image results
    mock_vector_store.query.return_value = [
        QueryResult(
            document=VectorDocument(
                id="test_id",
                content=b"test_image_data",
                metadata={
                    "content_type": "image",
                    "image_metadata": {
                        "format": "PNG",
                        "width": 100,
                        "height": 100,
                        "mode": "RGB"
                    },
                    "ocr_text": "Test text"
                },
                embedding=[0.1, 0.2, 0.3],
                timestamp=datetime.utcnow()
            ),
            score=0.95
        )
    ]
    
    # Query images using text
    results = await rag_service.query_images(
        query="test query",
        metadata_filters={"category": "image"}
    )
    
    # Verify operations
    mock_ai_provider.generate_embedding.assert_called_once_with("test query")
    mock_vector_store.query.assert_called_once()
    assert len(results) == 1
    assert isinstance(results[0][0], MemoryEntry)
    assert isinstance(results[0][0].content, ImageData)
    assert isinstance(results[0][1], float)

@pytest.mark.asyncio
async def test_query_images_image_to_image(
    rag_service,
    mock_vector_store,
    mock_ai_provider
):
    # Create test image
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    # Query images using image
    results = await rag_service.query_images(
        query=img_bytes,
        metadata_filters={"category": "image"}
    )
    
    # Verify operations
    mock_ai_provider.generate_embedding.assert_called_once_with(
        img_bytes,
        model="image-embed"
    )
    mock_vector_store.query.assert_called_once()
    assert len(results) == 1

@pytest.mark.asyncio
async def test_data_cleaning(rag_service):
    # Test text cleaning
    text = "  Test   content\nwith\tspaces  "
    cleaned_text = rag_service._clean_text(text)
    assert cleaned_text == "Test content with spaces"
    
    # Test structured data cleaning
    data = {
        "Key With Spaces": "  Test   value  ",
        "nested": {
            "Array Key": [
                {"Sub Key": "  value  "},
                "  test  "
            ]
        }
    }
    cleaned_data = rag_service._clean_structured_data(data)
    
    assert "key_with_spaces" in cleaned_data
    assert cleaned_data["key_with_spaces"] == "Test value"
    assert "nested" in cleaned_data
    assert "array_key" in cleaned_data["nested"]
    assert "sub_key" in cleaned_data["nested"]["array_key"][0]
    assert cleaned_data["nested"]["array_key"][0]["sub_key"] == "value"
    assert cleaned_data["nested"]["array_key"][1] == "test"

@pytest.mark.asyncio
async def test_error_handling(rag_service, mock_vector_store):
    # Configure mock to raise error
    mock_vector_store.add_documents.side_effect = VectorStoreError("Test error")
    
    # Test error handling
    with pytest.raises(VectorStoreError):
        await rag_service.store_text("Test content")

def test_schema_loading(tmp_path):
    # Create schema directory
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()
    
    # Create test schemas
    schemas = {
        "document": {
            "fields": {
                "type": {"type": "string", "required": True}
            },
            "version": "1.0.0"
        },
        "image": {
            "fields": {
                "format": {"type": "string", "required": True}
            },
            "version": "1.0.0"
        }
    }
    
    for name, schema in schemas.items():
        with open(schema_dir / f"{name}.json", "w") as f:
            json.dump(schema, f)
    
    # Create service and verify schema loading
    with patch("src.services.vector_store.factory.VectorStoreFactory.get_provider"):
        service = RAGMemoryService(
            store_type=VectorStoreType.CHROMA,
            connection_params={},
            ai_service_manager=MagicMock(),
            schema_dir=schema_dir
        )
        
        assert len(service.schemas) == 2
        assert "document" in service.schemas
        assert "image" in service.schemas 