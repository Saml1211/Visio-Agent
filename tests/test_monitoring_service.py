import pytest
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile
from unittest.mock import patch, Mock
import threading

from src.services.monitoring_service import MonitoringService, MonitoringConfig
from src.services.exceptions import PerformanceError

@pytest.fixture
def temp_log_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def config(temp_log_dir):
    return MonitoringConfig(
        metrics_port=0,
        performance_log=temp_log_dir / "performance.log",
        error_log=temp_log_dir / "error.log",
        health_check_interval=0.1,
        memory_threshold=0.9,
        cpu_threshold=0.8,
        response_time_threshold=1.0,
        error_threshold=5,
        max_error_history=10,
        thread_idle_threshold=10
    )

@pytest.fixture
def monitoring_service(config):
    with patch('prometheus_client.start_http_server'):
        service = MonitoringService(config)
        yield service
        service.stop()

def test_init(monitoring_service, config):
    """Test service initialization"""
    assert monitoring_service.config == config
    assert config.performance_log.parent.exists()
    assert config.error_log.parent.exists()

def test_operation_tracking(monitoring_service):
    """Test operation tracking functionality"""
    operation_id = "test_op_1"
    operation_type = "test_operation"
    
    monitoring_service.start_operation(operation_id, operation_type)
    assert operation_id in monitoring_service._start_times
    
    time.sleep(0.1)
    
    monitoring_service.end_operation(operation_id, operation_type)
    assert operation_id not in monitoring_service._start_times
    
    stats = monitoring_service.get_stats()
    assert operation_type in stats["operations"]
    assert stats["operations"][operation_type]["count"] == 1
    assert stats["operations"][operation_type]["total_time"] > 0

def test_error_logging(monitoring_service, config):
    """Test error logging functionality"""
    error_type = "test_error"
    error_message = "Test error message"
    context = {"detail": "Additional info"}
    
    monitoring_service.log_error(error_type, error_message, **context)
    
    with open(config.error_log) as f:
        log_entry = json.loads(f.readline())
        assert log_entry["type"] == error_type
        assert log_entry["message"] == error_message
        assert log_entry["context"] == context
    
    stats = monitoring_service.get_error_stats()
    assert stats["total_counts"][error_type] == 1
    assert len(stats["recent_errors"]) == 1
    assert stats["last_minute"][error_type] == 1

def test_performance_alerts(monitoring_service):
    """Test performance alerts for slow operations"""
    operation_id = "slow_op"
    operation_type = "slow_operation"
    
    monitoring_service.start_operation(operation_id, operation_type)
    time.sleep(monitoring_service.config.response_time_threshold + 0.1)
    monitoring_service.end_operation(operation_id, operation_type)
    
    alerts = monitoring_service.get_alerts()
    assert len(alerts) == 1
    assert "Slow operation" in alerts[0]["message"]
    assert alerts[0]["data"]["duration"] > monitoring_service.config.response_time_threshold

def test_error_rate_monitoring(monitoring_service):
    """Test error rate monitoring and alerts"""
    error_type = "test_error"
    
    # Generate errors just below threshold
    for _ in range(monitoring_service.config.error_threshold):
        monitoring_service.log_error(error_type)
    
    # No alerts should be present
    assert len(monitoring_service.get_alerts()) == 0
    
    # Generate one more error to exceed threshold
    monitoring_service.log_error(error_type)
    
    # Should have an alert now
    alerts = monitoring_service.get_alerts()
    assert len(alerts) == 1
    assert "High error rate" in alerts[0]["message"]
    assert alerts[0]["data"]["error_type"] == error_type

@pytest.mark.asyncio
async def test_health_check(monitoring_service):
    """Test health check monitoring"""
    with patch('psutil.Process') as mock_process:
        # Mock high memory usage
        mock_process.return_value.memory_percent.return_value = 95
        
        # Start monitoring
        monitoring_service.start()
        
        # Wait for health check
        await asyncio.sleep(monitoring_service.config.health_check_interval * 2)
        
        # Should have a memory alert
        alerts = monitoring_service.get_alerts()
        assert len(alerts) == 1
        assert "High memory usage" in alerts[0]["message"]

def test_error_history_limit(monitoring_service):
    """Test error history size limiting"""
    error_type = "test_error"
    
    # Generate more errors than max_error_history
    for i in range(monitoring_service.config.max_error_history + 5):
        monitoring_service.log_error(error_type, f"Error {i}")
    
    # Check error history size
    stats = monitoring_service.get_error_stats()
    assert len(stats["recent_errors"]) == monitoring_service.config.max_error_history

def test_error_cleanup(monitoring_service):
    """Test cleanup of old errors"""
    error_type = "test_error"
    
    # Generate some errors
    for _ in range(5):
        monitoring_service.log_error(error_type)
    
    # Manipulate timestamps to make errors old
    old_time = datetime.now() - timedelta(minutes=2)
    for error in monitoring_service._error_history:
        error["timestamp"] == old_time.isoformat()
    
    # Force cleanup by generating a new error
    monitoring_service.log_error(error_type)
    
    # Check that old errors were cleaned up
    stats = monitoring_service.get_error_stats()
    assert stats["last_minute"][error_type] == 1  # Only the new error

def test_concurrent_operations(monitoring_service):
    """Test handling of concurrent operations"""
    # Start multiple operations
    operations = [
        ("op1", "type1"),
        ("op2", "type1"),
        ("op3", "type2")
    ]
    
    for op_id, op_type in operations:
        monitoring_service.start_operation(op_id, op_type)
    
    # End operations in reverse order
    for op_id, op_type in reversed(operations):
        time.sleep(0.1)  # Simulate different durations
        monitoring_service.end_operation(op_id, op_type)
    
    # Check stats
    stats = monitoring_service.get_stats()
    assert stats["operations"]["type1"]["count"] == 2
    assert stats["operations"]["type2"]["count"] == 1

def test_memory_leak_detection(monitoring_service):
    """Test memory leak detection"""
    with patch('psutil.Process') as mock_process:
        # Simulate memory growth
        mock_process.return_value.memory_percent.side_effect = [
            10.0,  # Initial
            12.0,  # 20% growth
            11.9   # After GC
        ]
        
        # Force memory check
        monitoring_service._check_memory_growth()
        
        # Should have an alert
        alerts = monitoring_service.get_alerts()
        assert len(alerts) == 1
        assert "Potential memory leak" in alerts[0]["message"]
        assert alerts[0]["data"]["growth_percent"] == 20.0

def test_thread_monitoring(monitoring_service):
    """Test thread health monitoring"""
    # Create a mock thread
    mock_thread = Mock()
    mock_thread.ident = 12345
    
    with patch('threading.enumerate', return_value=[mock_thread]):
        # Initial check
        monitoring_service._check_thread_health()
        assert 12345 in monitoring_service._thread_history
        
        # Simulate thread being idle
        monitoring_service._thread_history[12345] = time.time() - monitoring_service.config.thread_idle_threshold - 1
        
        # Check again
        monitoring_service._check_thread_health()
        
        # Should have an alert
        alerts = monitoring_service.get_alerts()
        assert len(alerts) == 1
        assert "Potentially stuck thread" in alerts[0]["message"]
        assert alerts[0]["data"]["thread_id"] == 12345

def test_thread_cleanup(monitoring_service):
    """Test cleanup of finished threads"""
    # Add some thread history
    monitoring_service._thread_history = {
        1: time.time(),
        2: time.time()
    }
    
    # Mock only one thread still running
    mock_thread = Mock()
    mock_thread.ident = 1
    
    with patch('threading.enumerate', return_value=[mock_thread]):
        monitoring_service._check_thread_health()
        
        # Thread 2 should be removed
        assert 1 in monitoring_service._thread_history
        assert 2 not in monitoring_service._thread_history

def test_gc_trigger(monitoring_service):
    """Test garbage collection trigger on memory growth"""
    with patch('psutil.Process') as mock_process, \
         patch('gc.collect') as mock_gc:
        # Simulate memory growth
        mock_process.return_value.memory_percent.side_effect = [
            10.0,  # Initial
            12.0,  # 20% growth
            11.0   # After GC
        ]
        
        # Set last GC time to trigger collection
        monitoring_service._last_gc_collect = time.time() - 301
        
        # Force memory check
        monitoring_service._check_memory_growth()
        
        # Should have triggered GC
        mock_gc.assert_called_once()

@pytest.mark.asyncio
async def test_health_check_integration(monitoring_service):
    """Test integration of all health checks"""
    with patch('psutil.Process') as mock_process, \
         patch('psutil.cpu_percent') as mock_cpu:
        # Set up mocks
        mock_process.return_value.memory_percent.return_value = 95  # High memory
        mock_cpu.return_value = 90  # High CPU
        
        # Start monitoring
        monitoring_service.start()
        
        # Wait for health check
        await asyncio.sleep(monitoring_service.config.health_check_interval * 2)
        
        # Stop monitoring
        monitoring_service.stop()
        
        # Should have multiple alerts
        alerts = monitoring_service.get_alerts()
        alert_messages = [a["message"] for a in alerts]
        
        assert any("High memory usage" in msg for msg in alert_messages)
        assert any("High CPU usage" in msg for msg in alert_messages)

def test_metrics_reporting(monitoring_service):
    """Test Prometheus metrics reporting"""
    # Record some operations
    monitoring_service.start_operation("test1", "query")
    time.sleep(0.1)
    monitoring_service.end_operation("test1", "query")
    
    monitoring_service.log_error("test_error")
    
    # Check metrics
    assert monitoring_service.request_counter.labels(type="query")._value.get() == 1
    assert monitoring_service.error_counter.labels(type="test_error")._value.get() == 1
    assert monitoring_service.response_time.labels(type="query")._count.get() == 1

def test_alert_rate_limiting(monitoring_service):
    """Test that similar alerts are rate limited"""
    # Generate multiple high memory alerts
    for _ in range(5):
        monitoring_service._handle_performance_alert(
            "High memory usage detected",
            actual=95,
            threshold=90
        )
        time.sleep(0.1)
    
    # Should have fewer alerts due to rate limiting
    alerts = monitoring_service.get_alerts()
    memory_alerts = [a for a in alerts if "High memory usage" in a["message"]]
    assert len(memory_alerts) < 5

def test_alert_statistics(monitoring_service):
    """Test alert statistics tracking"""
    # Generate some alerts
    alerts = [
        ("High memory usage", {"actual": 95, "threshold": 90}),
        ("High memory usage", {"actual": 96, "threshold": 90}),
        ("High CPU usage", {"actual": 85, "threshold": 80}),
        ("Slow operation", {"duration": 6.0, "threshold": 5.0})
    ]
    
    for message, data in alerts:
        monitoring_service._handle_performance_alert(message, **data)
    
    # Get alert stats
    stats = monitoring_service.get_alert_stats()
    
    # Check alert counts
    assert stats["alert_counts"]["High memory usage"] == 2
    assert stats["alert_counts"]["High CPU usage"] == 1
    assert stats["alert_counts"]["Slow operation"] == 1
    
    # Check rate limiting
    assert stats["rate_limited"] > 0
    
    # Check active alerts
    assert len(stats["active_alerts"]) > 0 