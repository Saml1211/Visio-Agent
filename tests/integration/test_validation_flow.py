import pytest
import asyncio
from pathlib import Path
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, patch
import json

from src.services.deep_validator import DeepValidator, ValidationResult
from src.services.monitoring_service import MonitoringService, MonitoringConfig
from src.services.rag_memory_service import RAGMemoryService
from src.services.exceptions import ValidationError

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def monitoring_config(temp_dir):
    return MonitoringConfig(
        metrics_port=0,
        performance_log=temp_dir / "performance.log",
        error_log=temp_dir / "error.log",
        health_check_interval=0.1
    )

@pytest.fixture
def monitoring_service(monitoring_config):
    service = MonitoringService(monitoring_config)
    service.start()
    yield service
    service.stop()

@pytest.fixture
def mock_rag_memory():
    mock = AsyncMock()
    mock.store_validation_result = AsyncMock()
    mock.query_memory = AsyncMock(return_value=[])
    return mock

@pytest.fixture
async def validator(monitoring_service, mock_rag_memory):
    validator = DeepValidator(config={
        "min_element_spacing": 20,
        "min_font_size": 8
    })
    return validator

@pytest.mark.asyncio
async def test_full_validation_flow(validator, monitoring_service, mock_rag_memory):
    """Test complete validation flow with monitoring"""
    # Test data
    diagram_data = {
        "elements": [
            {
                "id": "elem1",
                "position": {"x": 0, "y": 0},
                "size": {"width": 100, "height": 50},
                "text": "Test Element 1",
                "font_size": 12,
                "fill_color": "#000000"
            },
            {
                "id": "elem2",
                "position": {"x": 200, "y": 0},
                "size": {"width": 100, "height": 50},
                "text": "Test Element 2",
                "font_size": 10,
                "fill_color": "#FFFFFF"
            }
        ]
    }
    
    # Start monitoring operation
    operation_id = "test_validation_1"
    monitoring_service.start_operation(operation_id, "diagram_validation")
    
    try:
        # Perform validation
        result = await validator.validate_diagram(diagram_data)
        
        # Verify validation result
        assert isinstance(result, ValidationResult)
        assert result.passed
        assert len(result.issues) == 0
        
        # Verify monitoring metrics
        stats = monitoring_service.get_stats()
        assert "diagram_validation" in stats["operations"]
        assert stats["operations"]["diagram_validation"]["count"] > 0
        
        # Verify RAG memory storage
        mock_rag_memory.store_validation_result.assert_called_once()
        stored_data = mock_rag_memory.store_validation_result.call_args[0][0]
        assert stored_data["passed"] == result.passed
        
    finally:
        monitoring_service.end_operation(operation_id, "diagram_validation")

@pytest.mark.asyncio
async def test_error_recovery(validator, monitoring_service, mock_rag_memory):
    """Test error recovery in validation flow"""
    # Configure mock to fail initially
    mock_rag_memory.store_validation_result.side_effect = [
        Exception("Storage error"),
        None  # Succeed on retry
    ]
    
    diagram_data = {
        "elements": [
            {
                "id": "elem1",
                "text": "Test",
                "font_size": 12
            }
        ]
    }
    
    operation_id = "test_validation_2"
    monitoring_service.start_operation(operation_id, "diagram_validation")
    
    try:
        result = await validator.validate_diagram(diagram_data)
        
        # Verify error was logged
        error_stats = monitoring_service.get_error_stats()
        assert error_stats["total_counts"].get("storage_error", 0) > 0
        
        # Verify retry succeeded
        assert mock_rag_memory.store_validation_result.call_count == 2
        
    finally:
        monitoring_service.end_operation(operation_id, "diagram_validation")

@pytest.mark.asyncio
async def test_concurrent_validations(validator, monitoring_service, mock_rag_memory):
    """Test concurrent validation operations"""
    diagrams = [
        {
            "elements": [
                {
                    "id": f"elem{i}",
                    "text": f"Test {i}",
                    "font_size": 12
                }
            ]
        }
        for i in range(5)
    ]
    
    async def validate_with_monitoring(diagram, index):
        operation_id = f"test_validation_{index}"
        monitoring_service.start_operation(operation_id, "diagram_validation")
        try:
            return await validator.validate_diagram(diagram)
        finally:
            monitoring_service.end_operation(operation_id, "diagram_validation")
    
    # Run validations concurrently
    results = await asyncio.gather(*[
        validate_with_monitoring(diagram, i)
        for i, diagram in enumerate(diagrams)
    ])
    
    # Verify all validations completed
    assert len(results) == len(diagrams)
    assert all(isinstance(r, ValidationResult) for r in results)
    
    # Verify resource cleanup
    assert validator.resource_manager.active_validations == 0
    
    # Check monitoring stats
    stats = monitoring_service.get_stats()
    assert stats["operations"]["diagram_validation"]["count"] == len(diagrams)

@pytest.mark.asyncio
async def test_performance_benchmarks(validator, monitoring_service):
    """Test validation performance under load"""
    # Generate large diagram
    large_diagram = {
        "elements": [
            {
                "id": f"elem{i}",
                "position": {"x": i*100, "y": 0},
                "size": {"width": 50, "height": 50},
                "text": f"Test Element {i}",
                "font_size": 10,
                "fill_color": "#000000",
                "rotation": i * 45
            }
            for i in range(100)  # 100 elements
        ]
    }
    
    operation_id = "perf_test"
    monitoring_service.start_operation(operation_id, "diagram_validation")
    
    try:
        start_time = datetime.now()
        result = await validator.validate_diagram(large_diagram)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Verify performance
        assert duration < 5.0  # Should complete within 5 seconds
        
        # Check memory usage
        stats = monitoring_service.get_stats()
        assert stats["memory_usage"] < 90.0  # Memory usage should stay reasonable
        
        # Verify all elements were processed
        assert len(result.issues) >= 0  # Should have processed all elements
        
    finally:
        monitoring_service.end_operation(operation_id, "diagram_validation")

@pytest.mark.asyncio
async def test_validation_with_recovery_points(validator, mock_rag_memory):
    """Test validation with intermediate recovery points"""
    large_diagram = {
        "elements": [{"id": f"elem{i}"} for i in range(50)]
    }
    
    # Simulate periodic storage of intermediate results
    results = []
    batch_size = 10
    
    for i in range(0, len(large_diagram["elements"]), batch_size):
        batch = {
            "elements": large_diagram["elements"][i:i+batch_size]
        }
        
        result = await validator.validate_diagram(batch)
        results.append(result)
        
        # Store recovery point
        await mock_rag_memory.store_validation_result(
            {
                "batch_index": i // batch_size,
                "result": result.__dict__,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    # Verify all batches were processed
    assert len(results) == len(large_diagram["elements"]) // batch_size
    assert all(r.passed for r in results)
    
    # Verify recovery points were stored
    assert mock_rag_memory.store_validation_result.call_count == len(results) 