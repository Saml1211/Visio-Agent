import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json
import numpy as np

from src.services.self_learning_service import (
    SelfLearningService,
    FeedbackEntry,
    FineTuningMetrics
)
from src.services.ai_service_config import AIServiceManager
from src.services.rag_memory_service import RAGMemoryService

@pytest.fixture
def mock_ai_provider():
    provider = MagicMock()
    provider.create_fine_tuning_job.return_value = "job_123"
    provider.get_fine_tuning_job.return_value = {
        "status": "succeeded",
        "result_model_id": "ft_model_123",
        "trained_tokens": 1000,
        "validation_accuracy": 0.95,
        "improvement_score": 0.2
    }
    provider.get_base_model.return_value = "base_model"
    provider.create_training_file.return_value = "file_123"
    return provider

@pytest.fixture
def mock_ai_service_manager(mock_ai_provider):
    manager = MagicMock(spec=AIServiceManager)
    manager.get_provider.return_value = mock_ai_provider
    manager.get_default_provider.return_value = mock_ai_provider
    return manager

@pytest.fixture
def mock_rag_memory():
    memory = MagicMock(spec=RAGMemoryService)
    memory.store_entry.return_value = "entry_123"
    memory.store_image.return_value = "image_123"
    memory.query_memory.return_value = [
        MagicMock(
            content='{"input": "test", "expected": "test", "actual": "test"}',
            metadata={"confidence_score": 0.8}
        )
    ]
    return memory

@pytest.fixture
def self_learning_service(mock_ai_service_manager, mock_rag_memory):
    return SelfLearningService(
        ai_service_manager=mock_ai_service_manager,
        rag_memory=mock_rag_memory,
        feedback_threshold=2,
        min_confidence_threshold=0.8
    )

def test_process_feedback_text(self_learning_service, mock_rag_memory):
    # Process text feedback
    entry_id = self_learning_service.process_feedback(
        feedback_type="text",
        input_data="test input",
        expected_output="expected",
        actual_output="actual",
        user_feedback="needs improvement",
        confidence_score=0.7
    )
    
    # Verify operations
    assert entry_id == "entry_123"
    mock_rag_memory.store_entry.assert_called_once()
    stored_content = json.loads(mock_rag_memory.store_entry.call_args[1]["content"])
    assert stored_content["input"] == "test input"
    assert stored_content["expected"] == "expected"

def test_process_feedback_image(self_learning_service, mock_rag_memory):
    # Process image feedback
    entry_id = self_learning_service.process_feedback(
        feedback_type="image",
        input_data=b"test_image",
        expected_output="expected",
        actual_output="actual",
        user_feedback="needs improvement",
        confidence_score=0.7
    )
    
    # Verify operations
    assert entry_id == "image_123"
    mock_rag_memory.store_image.assert_called_once()
    stored_metadata = mock_rag_memory.store_image.call_args[1]["metadata"]
    assert stored_metadata["expected_output"] == "expected"
    assert stored_metadata["actual_output"] == "actual"

def test_retrieve_relevant_knowledge(self_learning_service, mock_rag_memory):
    # Retrieve knowledge
    results = self_learning_service.retrieve_relevant_knowledge(
        context="test context",
        feedback_type="text"
    )
    
    # Verify operations
    assert len(results) == 1
    mock_rag_memory.query_memory.assert_called_once()
    query_filters = mock_rag_memory.query_memory.call_args[1]["filters"]
    assert query_filters["type"] == "feedback"
    assert query_filters["feedback_type"] == "text"

def test_fine_tune_model_success(self_learning_service, mock_ai_provider):
    # Configure mock to return sufficient samples
    self_learning_service.rag_memory.query_memory.return_value = [
        MagicMock() for _ in range(3)  # More than threshold
    ]
    
    # Fine-tune model
    metrics = self_learning_service.fine_tune_model("text")
    
    # Verify operations
    assert isinstance(metrics, FineTuningMetrics)
    assert metrics.model_id == "ft_model_123"
    assert metrics.validation_accuracy == 0.95
    mock_ai_provider.create_fine_tuning_job.assert_called_once()

def test_fine_tune_model_insufficient_samples(self_learning_service):
    # Configure mock to return insufficient samples
    self_learning_service.rag_memory.query_memory.return_value = [MagicMock()]
    
    # Attempt fine-tuning
    metrics = self_learning_service.fine_tune_model("text")
    
    # Verify operations
    assert metrics is None

def test_fine_tune_model_failure(self_learning_service, mock_ai_provider):
    # Configure mock for failure
    mock_ai_provider.get_fine_tuning_job.return_value = {
        "status": "failed",
        "error": "Test error"
    }
    
    # Configure mock to return sufficient samples
    self_learning_service.rag_memory.query_memory.return_value = [
        MagicMock() for _ in range(3)
    ]
    
    # Attempt fine-tuning
    with pytest.raises(Exception) as exc_info:
        self_learning_service.fine_tune_model("text")
    
    assert "Test error" in str(exc_info.value)

def test_should_fine_tune(self_learning_service):
    # Configure mock for low confidence
    self_learning_service.rag_memory.query_memory.return_value = [
        MagicMock(metadata={"confidence_score": 0.6}) for _ in range(3)
    ]
    
    # Check fine-tuning condition
    should_fine_tune = self_learning_service._should_fine_tune("text")
    
    # Verify result
    assert should_fine_tune is True

def test_should_not_fine_tune_high_confidence(self_learning_service):
    # Configure mock for high confidence
    self_learning_service.rag_memory.query_memory.return_value = [
        MagicMock(metadata={"confidence_score": 0.9}) for _ in range(3)
    ]
    
    # Check fine-tuning condition
    should_fine_tune = self_learning_service._should_fine_tune("text")
    
    # Verify result
    assert should_fine_tune is False

def test_prepare_training_data(self_learning_service, mock_ai_provider):
    # Test data
    training_data = [
        {
            "input": "test input",
            "expected": "expected output",
            "feedback": "needs improvement"
        }
    ]
    
    # Prepare training data
    file_id = self_learning_service._prepare_training_data(training_data)
    
    # Verify operations
    assert file_id == "file_123"
    mock_ai_provider.create_training_file.assert_called_once()

def test_monitor_fine_tuning_timeout(self_learning_service, mock_ai_provider):
    # Configure service with short timeout
    self_learning_service.max_training_duration = 0
    
    # Configure mock for running status
    mock_ai_provider.get_fine_tuning_job.return_value = {
        "status": "running"
    }
    
    # Attempt monitoring
    with pytest.raises(Exception) as exc_info:
        self_learning_service._monitor_fine_tuning("job_123", mock_ai_provider)
    
    assert "timeout exceeded" in str(exc_info.value)

def test_calculate_average_confidence(self_learning_service):
    # Configure mock with mixed confidence scores
    self_learning_service.rag_memory.query_memory.return_value = [
        MagicMock(metadata={"confidence_score": 0.8}),
        MagicMock(metadata={"confidence_score": 0.6})
    ]
    
    # Calculate average confidence
    avg_confidence = self_learning_service._calculate_average_confidence("text")
    
    # Verify result
    assert avg_confidence == 0.7

def test_error_handling(self_learning_service, mock_rag_memory):
    # Configure mock to raise error
    mock_rag_memory.store_entry.side_effect = Exception("Test error")
    
    # Attempt to process feedback
    with pytest.raises(Exception) as exc_info:
        self_learning_service.process_feedback(
            feedback_type="text",
            input_data="test",
            expected_output="test",
            actual_output="test",
            user_feedback="test",
            confidence_score=0.8
        )
    
    assert "Test error" in str(exc_info.value) 