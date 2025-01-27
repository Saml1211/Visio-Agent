import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.models.document_models import ProcessedContent, AVComponent
from src.services.llm_ai_service import LLMBasedAIService

@pytest.fixture
def mock_openai():
    with patch('openai.ChatCompletion') as mock:
        yield mock

@pytest.fixture
def ai_service():
    return LLMBasedAIService(api_key="test_key", model="gpt-4", temperature=0.7)

@pytest.fixture
def sample_processed_content():
    return ProcessedContent(
        raw_text="Sample AV system with projector and screen",
        structured_data={
            "components": [
                {"type": "projector", "model": "Epson Pro L25000U"},
                {"type": "screen", "model": "Da-Lite Tensioned Advantage"}
            ]
        },
        extracted_entities=[],
        confidence_score=0.8,
        processing_metadata={}
    )

@pytest.fixture
def sample_components():
    return [
        AVComponent(
            id="proj1",
            name="Main Projector",
            type="projector",
            manufacturer="Epson",
            model="Pro L25000U",
            specifications={"lumens": 25000, "resolution": "4K"},
            connections=[{"type": "HDMI", "count": 2}],
            position={"x": 100, "y": 100},
            attributes={"mounting": "ceiling"}
        ),
        AVComponent(
            id="screen1",
            name="Main Screen",
            type="screen",
            manufacturer="Da-Lite",
            model="Tensioned Advantage",
            specifications={"size": "150inch", "aspect_ratio": "16:9"},
            connections=[],
            position={"x": 300, "y": 100},
            attributes={"mounting": "wall"}
        )
    ]

@pytest.mark.asyncio
async def test_analyze_content_success(mock_openai, ai_service, sample_processed_content):
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="""{
            "entities": [
                {
                    "type": "projector",
                    "model": "Epson Pro L25000U",
                    "specifications": {"lumens": 25000}
                }
            ],
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.9
        }"""))
    ]
    mock_openai.acreate.return_value = mock_response
    
    # Test the analyze_content method
    result = await ai_service.analyze_content(sample_processed_content)
    
    assert result is not None
    assert "entities" in result
    assert "confidence_score" in result
    assert result["confidence_score"] >= 0.0
    assert result["confidence_score"] <= 1.0

@pytest.mark.asyncio
async def test_map_relationships_success(mock_openai, ai_service):
    # Test data
    entities = [
        {"id": "proj1", "type": "projector"},
        {"id": "screen1", "type": "screen"}
    ]
    
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="[]"))
    ]
    mock_openai.acreate.return_value = mock_response
    
    # Test the map_relationships method
    result = await ai_service.map_relationships(entities)
    
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_plan_layout_success(mock_openai, ai_service, sample_components):
    # Mock OpenAI response
    mock_response = Mock()
    mock_response.choices = [
        Mock(message=Mock(content="""{
            "layout": {
                "components": [
                    {"id": "proj1", "position": {"x": 100, "y": 100}},
                    {"id": "screen1", "position": {"x": 300, "y": 100}}
                ]
            },
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.9
        }"""))
    ]
    mock_openai.acreate.return_value = mock_response
    
    # Test the plan_layout method
    result = await ai_service.plan_layout(sample_components)
    
    assert result is not None
    assert "layout" in result
    assert "confidence_score" in result

@pytest.mark.asyncio
async def test_analyze_content_error(mock_openai, ai_service, sample_processed_content):
    mock_openai.acreate.side_effect = Exception("API Error")
    with pytest.raises(Exception) as exc_info:
        await ai_service.analyze_content(sample_processed_content)
    assert "API Error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_map_relationships_error(mock_openai, ai_service):
    # Mock OpenAI error
    mock_openai.acreate.side_effect = Exception("API Error")
    
    # Test error handling
    with pytest.raises(Exception):
        await ai_service.map_relationships([])

@pytest.mark.asyncio
async def test_plan_layout_error(mock_openai, ai_service, sample_components):
    # Mock OpenAI error
    mock_openai.acreate.side_effect = Exception("API Error")
    
    # Test error handling
    with pytest.raises(Exception):
        await ai_service.plan_layout(sample_components)

def test_create_analysis_prompt(ai_service, sample_processed_content):
    prompt = ai_service._create_analysis_prompt(sample_processed_content)
    assert isinstance(prompt, str)
    assert "Raw Text" in prompt
    assert "Existing Structured Data" in prompt

def test_create_relationship_prompt(ai_service):
    entities = [{"id": "test", "type": "projector"}]
    prompt = ai_service._create_relationship_prompt(entities)
    assert isinstance(prompt, str)
    assert "Components" in prompt

def test_create_layout_prompt(ai_service, sample_components):
    prompt = ai_service._create_layout_prompt(sample_components)
    assert isinstance(prompt, str)
    assert "Components" in prompt 