import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.models.document_models import (
    Document, DocumentMetadata, ProcessedContent,
    DocumentType, ProcessingStatus, AVComponent
)
from src.workflows.av_system_workflow import AVSystemWorkflow
from src.services.ai_refinement_service import RefinementType

@pytest.fixture
def sample_document():
    return Document(
        id="doc1",
        metadata=DocumentMetadata(
            file_name="test.pdf",
            file_type=DocumentType.PDF,
            file_size=1000,
            upload_date=datetime.now(),
            last_modified=datetime.now(),
            mime_type="application/pdf",
            checksum="abc123"
        ),
        status=ProcessingStatus.PENDING,
        content=ProcessedContent(
            raw_text="Test AV system document",
            structured_data={
                "entities": [
                    {
                        "type": "projector",
                        "name": "Main Projector",
                        "manufacturer": "Epson",
                        "model": "Pro L25000U",
                        "specifications": {"lumens": 25000}
                    }
                ]
            },
            extracted_entities=[],
            confidence_score=0.8,
            processing_metadata={}
        )
    )

@pytest.fixture
def mock_ai_service():
    with patch('src.services.llm_ai_service.LLMBasedAIService') as mock:
        # Mock analyze_content
        mock.return_value.analyze_content.return_value = {
            "entities": [],
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.9
        }
        
        # Mock map_relationships
        mock.return_value.map_relationships.return_value = []
        
        # Mock plan_layout
        mock.return_value.plan_layout.return_value = {
            "layout": {},
            "issues": [],
            "suggestions": [],
            "confidence_score": 0.9
        }
        
        yield mock

@pytest.fixture
def mock_visio_service():
    with patch('src.services.visio_generation_service.VisioGenerationService') as mock:
        yield mock

@pytest.fixture
def workflow(mock_ai_service):
    return AVSystemWorkflow(
        api_key="test_key",
        storage_path="/test/storage"
    )

@pytest.mark.asyncio
async def test_process_document_success(workflow, sample_document):
    # Test processing a document
    result = await workflow.process_document(sample_document)
    
    assert result is not None
    assert "workflow" in result
    assert "processed_content" in result
    assert "components" in result
    assert "layout" in result
    assert "data_history" in result
    assert "layout_history" in result

@pytest.mark.asyncio
async def test_refine_technical_data(workflow, sample_document):
    # Test technical data refinement
    processed_content, history = await workflow._refine_technical_data(sample_document)
    
    assert processed_content is not None
    assert isinstance(history, list)
    assert processed_content.confidence_score >= 0.0
    assert processed_content.confidence_score <= 1.0

@pytest.mark.asyncio
async def test_extract_components(workflow, sample_document):
    # Test component extraction
    components = await workflow._extract_components(sample_document.content)
    
    assert isinstance(components, list)
    assert len(components) > 0
    assert all(isinstance(comp, AVComponent) for comp in components)

@pytest.mark.asyncio
async def test_generate_visio_layout(workflow):
    # Test data
    components = [
        AVComponent(
            id="proj1",
            name="Main Projector",
            type="projector",
            manufacturer="Epson",
            model="Pro L25000U",
            specifications={"lumens": 25000},
            connections=[],
            position={"x": 0, "y": 0},
            attributes={}
        )
    ]
    
    # Test layout generation
    layout, history = await workflow._generate_visio_layout(components)
    
    assert layout is not None
    assert isinstance(history, list)

@pytest.mark.asyncio
async def test_create_workflow_record(workflow, sample_document):
    # Test data
    processed_content = sample_document.content
    components = []
    layout = {}
    data_history = []
    layout_history = []
    
    # Test workflow record creation
    workflow_record = workflow._create_workflow_record(
        sample_document,
        processed_content,
        components,
        layout,
        data_history,
        layout_history
    )
    
    assert workflow_record is not None
    assert workflow_record.id.startswith("workflow_")
    assert len(workflow_record.steps) == 3
    assert len(workflow_record.transitions) == 2

@pytest.mark.asyncio
async def test_process_document_error_handling(workflow, sample_document):
    # Mock an error in data refinement
    workflow.data_refinement.refine_technical_data.side_effect = Exception("Test error")
    
    # Test error handling
    with pytest.raises(Exception):
        await workflow.process_document(sample_document)

@pytest.mark.asyncio
async def test_workflow_with_empty_document(workflow):
    # Test processing a document with no content
    empty_document = Document(
        id="empty1",
        metadata=DocumentMetadata(
            file_name="empty.pdf",
            file_type=DocumentType.PDF,
            file_size=0,
            upload_date=datetime.now(),
            last_modified=datetime.now(),
            mime_type="application/pdf",
            checksum="empty123"
        ),
        status=ProcessingStatus.PENDING
    )
    
    result = await workflow.process_document(empty_document)
    assert result is not None
    assert "workflow" in result

@pytest.mark.asyncio
async def test_workflow_with_multiple_components(workflow, sample_document):
    # Add multiple components to the document
    sample_document.content.structured_data["entities"].extend([
        {
            "type": "screen",
            "name": "Main Screen",
            "manufacturer": "Da-Lite",
            "model": "Tensioned Advantage",
            "specifications": {"size": "150inch"}
        },
        {
            "type": "audio",
            "name": "Speaker System",
            "manufacturer": "JBL",
            "model": "Control 28",
            "specifications": {"power": "200W"}
        }
    ])
    
    result = await workflow.process_document(sample_document)
    components = result["components"]
    
    assert len(components) == 3
    assert len([c for c in components if c.type == "projector"]) == 1
    assert len([c for c in components if c.type == "screen"]) == 1
    assert len([c for c in components if c.type == "audio"]) == 1 