import pytest
from pathlib import Path
import tempfile
import json
import aiofiles
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from src.services.data_mapping_service import (
    DataMappingService,
    MappingType,
    MappingExample,
    MappingResult,
    ValidationError
)

@pytest.fixture
def temp_examples_dir():
    """Create a temporary directory for mapping examples"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_rag_memory():
    """Create a mock RAG memory service"""
    mock = Mock()
    mock.store_entry = AsyncMock()
    mock.query_memory = AsyncMock(return_value=None)
    return mock

@pytest.fixture
async def mapping_service(temp_examples_dir, mock_rag_memory):
    """Create a test mapping service"""
    service = DataMappingService(
        rag_memory=mock_rag_memory,
        examples_dir=temp_examples_dir
    )
    return service

@pytest.fixture
async def sample_examples(temp_examples_dir):
    """Create sample mapping examples"""
    examples = [
        {
            "source_data": {
                "device": {
                    "name": "Projector X1000",
                    "type": "projector",
                    "specs": {
                        "lumens": 5000,
                        "resolution": "4K"
                    }
                }
            },
            "target_fields": {
                "shape_name": "Projector X1000",
                "shape_type": "projector_4k",
                "properties": {
                    "brightness": "5000lm",
                    "display_res": "3840x2160"
                }
            },
            "explanation": "Mapped projector specs to Visio shape properties",
            "confidence_score": 0.95,
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    # Create examples file
    examples_file = temp_examples_dir / "component_examples.json"
    async with aiofiles.open(examples_file, 'w') as f:
        await f.write(json.dumps(examples))
    
    return examples

@pytest.mark.asyncio
async def test_load_mapping_examples(mapping_service, sample_examples):
    """Test loading mapping examples from file"""
    await mapping_service.load_mapping_examples()
    
    assert MappingType.COMPONENT in mapping_service.mapping_examples
    examples = mapping_service.mapping_examples[MappingType.COMPONENT]
    assert len(examples) == 1
    
    example = examples[0]
    assert example.source_data["device"]["name"] == "Projector X1000"
    assert example.target_fields["shape_name"] == "Projector X1000"
    assert example.confidence_score == 0.95

@pytest.mark.asyncio
async def test_save_mapping_examples(mapping_service):
    """Test saving mapping examples to file"""
    # Add example
    example = MappingExample(
        source_data={"field": "value"},
        target_fields={"shape_field": "value"},
        explanation="Test mapping",
        confidence_score=0.9,
        timestamp=datetime.now()
    )
    mapping_service.add_mapping_example(MappingType.CONNECTION, example)
    
    # Save examples
    await mapping_service.save_mapping_examples(MappingType.CONNECTION)
    
    # Check file exists
    examples_file = mapping_service.examples_dir / "connection_examples.json"
    assert examples_file.exists()
    
    # Verify contents
    async with aiofiles.open(examples_file, 'r') as f:
        content = await f.read()
        examples = json.loads(content)
        assert len(examples) == 1
        assert examples[0]["source_data"] == {"field": "value"}
        assert examples[0]["target_fields"] == {"shape_field": "value"}
        assert examples[0]["confidence_score"] == 0.9

@pytest.mark.asyncio
async def test_add_mapping_example(mapping_service):
    """Test adding a new mapping example"""
    example = MappingExample(
        source_data={"field": "value"},
        target_fields={"shape_field": "value"},
        explanation="Test mapping",
        confidence_score=0.9,
        timestamp=datetime.now()
    )
    
    mapping_service.add_mapping_example(MappingType.METADATA, example)
    
    assert MappingType.METADATA in mapping_service.mapping_examples
    examples = mapping_service.mapping_examples[MappingType.METADATA]
    assert len(examples) == 1
    assert examples[0].source_data == {"field": "value"}

@pytest.mark.asyncio
@patch('openai.ChatCompletion.acreate')
async def test_map_data_success(mock_openai, mapping_service, sample_examples):
    """Test successful data mapping"""
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="""{
            "mappings": [
                {
                    "source_field": "device.name",
                    "target_field": "shape_name",
                    "value": "Projector X1000",
                    "confidence_score": 0.95,
                    "explanation": "Direct name mapping"
                }
            ]
        }"""))
    ]
    mock_openai.return_value = mock_response
    
    # Test data
    source_data = {
        "device": {
            "name": "Projector X1000",
            "type": "projector"
        }
    }
    target_schema = {
        "shape_name": {"type": "string"},
        "shape_type": {"type": "string"}
    }
    
    # Load examples
    await mapping_service.load_mapping_examples()
    
    # Test mapping
    results = await mapping_service.map_data(
        source_data,
        target_schema,
        MappingType.COMPONENT
    )
    
    assert len(results) == 1
    assert results[0].source_field == "device.name"
    assert results[0].target_field == "shape_name"
    assert results[0].value == "Projector X1000"
    assert results[0].confidence_score == 0.95
    
    # Verify RAG memory was updated
    mapping_service.rag_memory.store_entry.assert_called_once()

@pytest.mark.asyncio
@patch('openai.ChatCompletion.acreate')
async def test_map_data_error(mock_openai, mapping_service):
    """Test error handling in data mapping"""
    # Mock OpenAI error
    mock_openai.side_effect = Exception("API Error")
    
    # Test data
    source_data = {"field": "value"}
    target_schema = {"shape_field": {"type": "string"}}
    
    # Test error handling
    with pytest.raises(Exception):
        await mapping_service.map_data(
            source_data,
            target_schema,
            MappingType.LAYOUT
        )

def test_apply_manual_override(mapping_service):
    """Test applying manual override to mapping result"""
    # Original mapping
    original = MappingResult(
        source_field="field",
        target_field="shape_field",
        value="old_value",
        confidence_score=0.8,
        mapping_type=MappingType.COMPONENT
    )
    
    # Apply override
    updated = mapping_service.apply_manual_override(original, "new_value")
    
    assert updated.value == "new_value"
    assert updated.confidence_score == 1.0
    assert updated.is_manual_override
    assert updated.source_field == original.source_field
    assert updated.target_field == original.target_field

def test_create_mapping_prompt(mapping_service):
    """Test mapping prompt creation"""
    source_data = {"field": "value"}
    target_schema = {"shape_field": {"type": "string"}}
    examples = [
        MappingExample(
            source_data={"test": "data"},
            target_fields={"shape": "data"},
            explanation="Test mapping",
            confidence_score=0.9,
            timestamp=datetime.now()
        )
    ]
    
    prompt = mapping_service._create_mapping_prompt(
        source_data,
        target_schema,
        examples
    )
    
    assert isinstance(prompt, str)
    assert "Source Data" in prompt
    assert "Target Schema" in prompt
    assert "Example 1" in prompt
    assert "Test mapping" in prompt

def test_parse_mapping_response_success(mapping_service):
    """Test successful parsing of mapping response"""
    response = """{
        "mappings": [
            {
                "source_field": "field",
                "target_field": "shape_field",
                "value": "mapped_value",
                "confidence_score": 0.9,
                "explanation": "Test mapping"
            }
        ]
    }"""
    
    results = mapping_service._parse_mapping_response(
        response,
        MappingType.COMPONENT
    )
    
    assert len(results) == 1
    assert results[0].source_field == "field"
    assert results[0].target_field == "shape_field"
    assert results[0].value == "mapped_value"
    assert results[0].confidence_score == 0.9

def test_parse_mapping_response_error(mapping_service):
    """Test error handling in response parsing"""
    # Invalid JSON
    results = mapping_service._parse_mapping_response(
        "invalid json",
        MappingType.COMPONENT
    )
    assert len(results) == 0
    
    # Missing required fields
    results = mapping_service._parse_mapping_response(
        '{"mappings": [{"field": "value"}]}',
        MappingType.COMPONENT
    )
    assert len(results) == 0 