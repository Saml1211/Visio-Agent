import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
from pathlib import Path
import tempfile

from src.services.workflow_orchestrator import (
    RefinementOrchestrator,
    WorkflowStep,
    WorkflowResult
)
from src.services.ai_service_config import AIServiceManager
from src.services.rag_memory_service import RAGMemoryService
from src.services.visio_generation_service import VisioGenerationService
from src.services.self_learning_service import SelfLearningService

@pytest.fixture
def mock_ai_provider():
    provider = MagicMock()
    provider.analyze_content.return_value = {
        "confidence": 0.9,
        "components": [
            {"id": "comp1", "type": "server"},
            {"id": "comp2", "type": "database"}
        ]
    }
    return provider

@pytest.fixture
def mock_ai_service_manager(mock_ai_provider):
    manager = MagicMock(spec=AIServiceManager)
    manager.get_provider.return_value = mock_ai_provider
    return manager

@pytest.fixture
def mock_rag_memory():
    memory = MagicMock(spec=RAGMemoryService)
    memory.store_entry.return_value = "entry_123"
    memory.query_memory.return_value = [
        MagicMock(content='{"test": "data"}')
    ]
    return memory

@pytest.fixture
def mock_visio_service():
    service = MagicMock(spec=VisioGenerationService)
    service.generate_diagram.return_value = None
    return service

@pytest.fixture
def mock_self_learning():
    service = MagicMock(spec=SelfLearningService)
    service.retrieve_relevant_knowledge.return_value = [
        {"id": "knowledge1", "content": "test knowledge"}
    ]
    return service

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def orchestrator(
    mock_ai_service_manager,
    mock_rag_memory,
    mock_visio_service,
    mock_self_learning,
    temp_output_dir
):
    return RefinementOrchestrator(
        ai_service_manager=mock_ai_service_manager,
        rag_memory=mock_rag_memory,
        visio_service=mock_visio_service,
        self_learning_service=mock_self_learning,
        output_dir=temp_output_dir
    )

def test_process_document_success(orchestrator, temp_output_dir):
    # Create test document
    doc_path = temp_output_dir / "test.txt"
    doc_path.write_text("Test document content")
    
    # Process document
    result = orchestrator.process_document(
        document_path=doc_path,
        template_name="test_template"
    )
    
    # Verify result
    assert isinstance(result, WorkflowResult)
    assert result.status == "completed"
    assert len(result.steps) == 3
    assert all(step.status == "completed" for step in result.steps)
    assert result.visio_file_path is not None
    assert result.pdf_file_path is not None

def test_refine_technical_data(orchestrator, mock_ai_provider, temp_output_dir):
    # Create test document
    doc_path = temp_output_dir / "test.txt"
    doc_path.write_text("Test document content")
    
    # Refine data
    steps = []
    data = orchestrator._refine_technical_data(
        document_path=doc_path,
        workflow_id="test_workflow",
        additional_context={"test": "context"},
        steps=steps
    )
    
    # Verify operations
    assert len(steps) == 1
    assert steps[0].status == "completed"
    assert data["confidence"] == 0.9
    mock_ai_provider.analyze_content.assert_called()

def test_extract_components(orchestrator, mock_ai_provider):
    # Test data
    data = {"test": "data"}
    
    # Extract components
    steps = []
    components = orchestrator._extract_components(
        data=data,
        workflow_id="test_workflow",
        steps=steps
    )
    
    # Verify operations
    assert len(steps) == 1
    assert steps[0].status == "completed"
    assert len(components) == 2
    assert components[0]["type"] == "server"
    mock_ai_provider.analyze_content.assert_called()

def test_generate_visio_layout(
    orchestrator,
    mock_ai_provider,
    mock_visio_service,
    temp_output_dir
):
    # Test data
    components = [
        {"id": "comp1", "type": "server"},
        {"id": "comp2", "type": "database"}
    ]
    
    # Generate layout
    steps = []
    result = orchestrator._generate_visio_layout(
        components=components,
        template_name="test_template",
        workflow_id="test_workflow",
        steps=steps
    )
    
    # Verify operations
    assert len(steps) == 1
    assert steps[0].status == "completed"
    assert result["visio_path"].endswith(".vsdx")
    assert result["pdf_path"].endswith(".pdf")
    mock_visio_service.generate_diagram.assert_called_once()

def test_create_workflow_record(orchestrator, mock_rag_memory):
    # Test data
    workflow_id = "test_workflow"
    steps = [
        WorkflowStep(
            name="test_step",
            status="completed",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        )
    ]
    visio_result = {
        "visio_path": "/test/path.vsdx",
        "pdf_path": "/test/path.pdf"
    }
    raw_data = {"test": "data"}
    
    # Create record
    result = orchestrator._create_workflow_record(
        workflow_id=workflow_id,
        steps=steps,
        visio_result=visio_result,
        raw_data=raw_data
    )
    
    # Verify operations
    assert isinstance(result, WorkflowResult)
    assert result.workflow_id == workflow_id
    assert result.status == "completed"
    assert len(result.steps) == 1
    mock_rag_memory.store_entry.assert_called_once()

def test_process_document_error_handling(orchestrator, mock_ai_provider, temp_output_dir):
    # Configure mock to raise error
    mock_ai_provider.analyze_content.side_effect = Exception("Test error")
    
    # Create test document
    doc_path = temp_output_dir / "test.txt"
    doc_path.write_text("Test document content")
    
    # Test error handling
    with pytest.raises(Exception) as exc_info:
        orchestrator.process_document(
            document_path=doc_path,
            template_name="test_template"
        )
    
    assert "Test error" in str(exc_info.value)

def test_workflow_step_tracking(orchestrator, temp_output_dir):
    # Create test document
    doc_path = temp_output_dir / "test.txt"
    doc_path.write_text("Test document content")
    
    # Process document
    result = orchestrator.process_document(
        document_path=doc_path,
        template_name="test_template"
    )
    
    # Verify step tracking
    assert len(result.steps) == 3
    step_names = [s.name for s in result.steps]
    assert "data_refinement" in step_names
    assert "component_extraction" in step_names
    assert "visio_generation" in step_names
    
    for step in result.steps:
        assert step.start_time is not None
        assert step.end_time is not None
        assert step.metadata is not None

def test_workflow_with_additional_context(orchestrator, mock_ai_provider, temp_output_dir):
    # Create test document
    doc_path = temp_output_dir / "test.txt"
    doc_path.write_text("Test document content")
    
    # Additional context
    context = {
        "project_id": "test_project",
        "user_id": "test_user",
        "settings": {"key": "value"}
    }
    
    # Process document
    result = orchestrator.process_document(
        document_path=doc_path,
        template_name="test_template",
        additional_context=context
    )
    
    # Verify context was passed
    call_args = mock_ai_provider.analyze_content.call_args_list[0]
    assert "project_id" in call_args[1]["context"]
    assert call_args[1]["context"]["project_id"] == "test_project" 