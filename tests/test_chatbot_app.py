import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import json
import tempfile
import tkinter as tk
import time

from src.chatbot_app import ChatbotApp
from src.services.hotkey_service import HotkeyService, AppContext
from src.services.chatbot_service import ChatbotService
from src.ui.chatbot_window import ChatbotWindow

@pytest.fixture
def mock_ai_service():
    service = Mock()
    service.generate_text = AsyncMock(return_value="Test response")
    return service

@pytest.fixture
def mock_rag_memory():
    memory = Mock()
    memory.query_memory = AsyncMock(return_value="Test context")
    memory.add_interaction = AsyncMock()
    return memory

@pytest.fixture
def mock_visio_service():
    service = Mock()
    return service

@pytest.fixture
def temp_config():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        config = {
            "ai_service": {
                "provider": "test",
                "model": "test-model"
            },
            "rag_memory": {
                "vector_store_path": "test/path"
            },
            "chatbot": {
                "model_name": "test-model",
                "log_file": "test.log",
                "performance_log": "perf.log"
            },
            "ui": {
                "window_title": "Test Assistant"
            },
            "hotkey": {
                "activation_key": "ctrl+alt+q"
            },
            "logging": {
                "level": "INFO",
                "file": None
            }
        }
        json.dump(config, f)
        f.flush()
        yield Path(f.name)

@pytest.mark.asyncio
async def test_chatbot_service(mock_ai_service, mock_rag_memory, mock_visio_service):
    """Test ChatbotService functionality"""
    # Initialize service
    service = ChatbotService(
        config=Mock(),
        ai_service=mock_ai_service,
        rag_memory=mock_rag_memory,
        visio_service=mock_visio_service
    )
    
    # Test general query
    response = await service.handle_general_query("test query")
    assert response == "Test response"
    mock_rag_memory.query_memory.assert_called_once_with("test query")
    mock_ai_service.generate_text.assert_called_once()
    
    # Test Visio command
    response = await service.handle_visio_command("test command")
    assert response == "Command processed successfully"
    mock_rag_memory.query_memory.assert_called_with("test command")

def test_hotkey_service():
    """Test HotkeyService functionality"""
    # Initialize service
    config = Mock(activation_key="ctrl+alt+q")
    service = HotkeyService(config)
    
    # Test callbacks
    general_callback = Mock()
    visio_callback = Mock()
    
    service.register_callback(AppContext.GENERAL, general_callback)
    service.register_callback(AppContext.VISIO, visio_callback)
    
    # Test starting and stopping
    service.start()
    assert service.is_running
    
    service.stop()
    assert not service.is_running

@pytest.mark.asyncio
async def test_chatbot_window():
    """Test ChatbotWindow functionality"""
    # Initialize window
    config = Mock(
        window_title="Test Assistant",
        window_width=600,
        window_height=400
    )
    
    callback = AsyncMock()
    loop = asyncio.get_event_loop()
    
    window = ChatbotWindow(config, callback, loop)
    
    # Test message addition
    window.add_message("Test message")
    assert "Test message" in window.output_text.get("1.0", tk.END)
    
    # Test submit handling
    window.input_text.insert(0, "test query")
    window._handle_submit()
    await asyncio.sleep(0.1)  # Allow async callback to complete
    
    callback.assert_called_once_with("test query")
    
    # Cleanup
    window.stop()

@pytest.mark.asyncio
async def test_chatbot_app(temp_config, mock_ai_service, mock_rag_memory):
    """Test ChatbotApp integration"""
    with patch("src.chatbot_app.AIServiceManager", return_value=mock_ai_service), \
         patch("src.chatbot_app.RAGMemoryService", return_value=mock_rag_memory), \
         patch("src.chatbot_app.VisioGenerationService"), \
         patch("src.chatbot_app.ChatbotWindow"):
        
        # Initialize app
        app = ChatbotApp(temp_config)
        
        # Test user input handling
        await app._handle_user_input("test query")
        mock_ai_service.generate_text.assert_called_once()
        mock_rag_memory.add_interaction.assert_called_once()
        
        # Test hotkey handling
        app._handle_general_hotkey()
        app.ui.restore.assert_called_once()
        
        # Cleanup
        app.stop()

def test_performance_logging(temp_config, mock_ai_service, mock_rag_memory):
    """Test performance logging"""
    with patch("src.chatbot_app.AIServiceManager", return_value=mock_ai_service), \
         patch("src.chatbot_app.RAGMemoryService", return_value=mock_rag_memory), \
         patch("src.chatbot_app.VisioGenerationService"), \
         patch("src.chatbot_app.ChatbotWindow"):
        
        # Initialize app
        app = ChatbotApp(temp_config)
        
        # Create a test query that takes some time
        async def slow_query():
            start_time = time.time()
            await asyncio.sleep(0.1)  # Simulate work
            await app.chatbot_service._log_performance(
                "test_query",
                start_time,
                True
            )
        
        # Run the test query
        asyncio.run(slow_query())
        
        # Check performance log
        with open(app.chatbot_service.config.performance_log) as f:
            log_entry = json.loads(f.readline())
            assert log_entry["context"] == "test_query"
            assert log_entry["duration"] >= 0.1
            assert log_entry["success"] is True
        
        # Cleanup
        app.stop()

def test_error_handling(temp_config, mock_ai_service, mock_rag_memory):
    """Test error handling"""
    with patch("src.chatbot_app.AIServiceManager", return_value=mock_ai_service), \
         patch("src.chatbot_app.RAGMemoryService", return_value=mock_rag_memory), \
         patch("src.chatbot_app.VisioGenerationService"), \
         patch("src.chatbot_app.ChatbotWindow"):
        
        # Initialize app
        app = ChatbotApp(temp_config)
        
        # Simulate AI service error
        mock_ai_service.generate_text.side_effect = Exception("AI service error")
        
        # Test error handling
        async def test_error():
            await app._handle_user_input("test query")
        
        asyncio.run(test_error())
        
        # Verify error was logged
        app.ui.add_message.assert_called_with("Error: Failed to process query: AI service error")
        
        # Cleanup
        app.stop()

def test_config_validation(temp_config):
    """Test configuration validation"""
    # Test missing required config
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        json.dump({}, f)
        f.flush()
        
        with pytest.raises(SystemExit):
            ChatbotApp(Path(f.name))
    
    # Test invalid config values
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        config = {
            "ai_service": {
                "temperature": "invalid"  # Should be float
            }
        }
        json.dump(config, f)
        f.flush()
        
        with pytest.raises(SystemExit):
            ChatbotApp(Path(f.name))

def test_thread_safety(temp_config, mock_ai_service, mock_rag_memory):
    """Test thread safety of components"""
    with patch("src.chatbot_app.AIServiceManager", return_value=mock_ai_service), \
         patch("src.chatbot_app.RAGMemoryService", return_value=mock_rag_memory), \
         patch("src.chatbot_app.VisioGenerationService"), \
         patch("src.chatbot_app.ChatbotWindow"):
        
        # Initialize app
        app = ChatbotApp(temp_config)
        
        # Simulate concurrent requests
        async def concurrent_requests():
            tasks = []
            for i in range(10):
                tasks.append(app._handle_user_input(f"query {i}"))
            await asyncio.gather(*tasks)
        
        asyncio.run(concurrent_requests())
        
        # Verify all requests were handled
        assert mock_ai_service.generate_text.call_count == 10
        assert mock_rag_memory.add_interaction.call_count == 10
        
        # Cleanup
        app.stop() 