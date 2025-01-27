import pytest
from pathlib import Path
import json
import tempfile
from unittest.mock import Mock, AsyncMock, patch
import numpy as np
from src.services.ai_ensemble_service import (
    AIEnsembleService,
    EnsembleMethod,
    ModelWeight,
    EnsembleResult,
    EnsembleError
)
from src.services.ai_service_config import TaskType, AIServiceConfig

@pytest.fixture
def ensemble_config():
    """Sample ensemble configuration"""
    return {
        "component_extraction": {
            "method": "majority_vote",
            "models": [
                {
                    "model_name": "gpt-4",
                    "base_weight": 1.0,
                    "confidence_multiplier": 1.2,
                    "latency_penalty": 0.1
                },
                {
                    "model_name": "claude-2",
                    "base_weight": 0.8,
                    "confidence_multiplier": 1.0,
                    "latency_penalty": 0.05
                }
            ]
        },
        "relationship_analysis": {
            "method": "cross_validation",
            "models": [
                {
                    "model_name": "gpt-4",
                    "base_weight": 1.0
                },
                {
                    "model_name": "claude-2",
                    "base_weight": 0.8
                }
            ]
        }
    }

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for configurations"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
async def ensemble_service(temp_config_dir, ensemble_config):
    """Create a test ensemble service"""
    config_path = temp_config_dir / "ensemble_config.json"
    with open(config_path, "w") as f:
        json.dump(ensemble_config, f)
    
    ai_config = Mock(spec=AIServiceConfig)
    service = AIEnsembleService(ai_config, config_path)
    
    return service

@pytest.mark.asyncio
async def test_load_ensemble_config(ensemble_service, ensemble_config):
    """Test loading ensemble configuration"""
    # Check loaded configurations
    assert TaskType.COMPONENT_EXTRACTION in ensemble_service.ensembles
    assert TaskType.RELATIONSHIP_ANALYSIS in ensemble_service.ensembles
    
    # Check model weights
    component_weights = ensemble_service.ensembles[TaskType.COMPONENT_EXTRACTION]
    assert len(component_weights) == 2
    assert component_weights[0].model_name == "gpt-4"
    assert component_weights[0].base_weight == 1.0
    
    # Check ensemble methods
    assert ensemble_service.ensemble_methods[TaskType.COMPONENT_EXTRACTION] == EnsembleMethod.MAJORITY_VOTE
    assert ensemble_service.ensemble_methods[TaskType.RELATIONSHIP_ANALYSIS] == EnsembleMethod.CROSS_VALIDATION

@pytest.mark.asyncio
async def test_process_with_ensemble(ensemble_service):
    """Test processing input with model ensemble"""
    # Mock model processing
    ensemble_service._process_with_model = AsyncMock(
        side_effect=["Component A, B", "Component A, C"]
    )
    
    result = await ensemble_service.process_with_ensemble(
        TaskType.COMPONENT_EXTRACTION,
        "Test input"
    )
    
    assert isinstance(result, EnsembleResult)
    assert result.method_used == EnsembleMethod.MAJORITY_VOTE
    assert len(result.model_outputs) == 2
    assert result.confidence_score > 0

@pytest.mark.asyncio
async def test_process_with_ensemble_error(ensemble_service):
    """Test handling processing errors"""
    ensemble_service._process_with_model = AsyncMock(
        side_effect=Exception("Model error")
    )
    
    with pytest.raises(EnsembleError):
        await ensemble_service.process_with_ensemble(
            TaskType.COMPONENT_EXTRACTION,
            "Test input"
        )

@pytest.mark.asyncio
async def test_majority_vote_combination(ensemble_service):
    """Test majority vote output combination"""
    outputs = ["Result A", "Result A", "Result B"]
    weights = {
        "model1": 0.4,
        "model2": 0.3,
        "model3": 0.3
    }
    
    result, confidence = ensemble_service._majority_vote(outputs, weights)
    assert result == "Result A"
    assert confidence > 0.6

@pytest.mark.asyncio
async def test_weighted_average_combination(ensemble_service):
    """Test weighted average output combination"""
    outputs = ["1.5", "2.0", "1.8"]
    weights = {
        "model1": 0.4,
        "model2": 0.3,
        "model3": 0.3
    }
    
    result, confidence = ensemble_service._weighted_average(outputs, weights)
    assert isinstance(result, float)
    assert 1.5 <= result <= 2.0
    assert 0 <= confidence <= 1

@pytest.mark.asyncio
async def test_cross_validation_combination(ensemble_service):
    """Test cross-validation output combination"""
    outputs = [
        "Component A connects to B",
        "Component A is linked to B",
        "Component X connects to Y"
    ]
    weights = {
        "model1": 0.4,
        "model2": 0.3,
        "model3": 0.3
    }
    
    result, confidence = ensemble_service._cross_validation(outputs, weights)
    assert "Component A" in result
    assert confidence > 0

@pytest.mark.asyncio
async def test_sequential_combination(ensemble_service):
    """Test sequential output combination"""
    outputs = [
        "Initial analysis",
        "Additional details",
        "Final refinement"
    ]
    weights = {
        "model1": 0.5,
        "model2": 0.3,
        "model3": 0.2
    }
    
    result, confidence = ensemble_service._sequential_combine(outputs, weights)
    assert "Initial analysis" in result
    assert "Additional details" in result
    assert confidence > 0

@pytest.mark.asyncio
async def test_calculate_weights(ensemble_service):
    """Test weight calculation"""
    model_weights = [
        ModelWeight(model_name="model1", base_weight=1.0),
        ModelWeight(model_name="model2", base_weight=0.8)
    ]
    outputs = ["Result 1", None]  # Second model failed
    
    weights = ensemble_service._calculate_weights(model_weights, outputs)
    assert weights["model1"] > weights["model2"]
    assert sum(weights.values()) == pytest.approx(1.0)

@pytest.mark.asyncio
async def test_calculate_similarity():
    """Test string similarity calculation"""
    service = AIEnsembleService(Mock(), Mock())
    
    # Test exact match
    assert service._calculate_similarity("test", "test") == 1.0
    
    # Test partial match
    similarity = service._calculate_similarity("test string", "test data")
    assert 0 < similarity < 1
    
    # Test no match
    similarity = service._calculate_similarity("abc", "xyz")
    assert similarity == 0

@pytest.mark.asyncio
async def test_ensemble_logging(ensemble_service, caplog):
    """Test ensemble result logging"""
    # Mock processing
    ensemble_service._process_with_model = AsyncMock(
        return_value="Test result"
    )
    
    # Process with ensemble
    await ensemble_service.process_with_ensemble(
        TaskType.COMPONENT_EXTRACTION,
        "Test input"
    )
    
    # Check logs
    assert "Ensemble processing for component_extraction" in caplog.text
    assert "confidence" in caplog.text.lower()
    assert "processing time" in caplog.text.lower()

@pytest.mark.asyncio
async def test_invalid_task_type(ensemble_service):
    """Test handling invalid task type"""
    with pytest.raises(EnsembleError):
        await ensemble_service.process_with_ensemble(
            TaskType.FEEDBACK_ANALYSIS,  # Not configured
            "Test input"
        )

@pytest.mark.asyncio
async def test_all_models_failed(ensemble_service):
    """Test handling all models failing"""
    ensemble_service._process_with_model = AsyncMock(return_value=None)
    
    with pytest.raises(EnsembleError):
        await ensemble_service.process_with_ensemble(
            TaskType.COMPONENT_EXTRACTION,
            "Test input"
        ) 