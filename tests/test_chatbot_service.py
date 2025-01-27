import pytest
from unittest.mock import Mock, patch
import asyncio
from datetime import datetime

from src.services.chatbot_service import ChatbotService, ChatbotConfig
from src.services.exceptions import ChatbotError, ServiceError, RateLimitError

@pytest.fixture
def mock_ai_service():
    return Mock()

@pytest.fixture
def mock_rag_memory():
    return Mock()

@pytest.fixture
def mock_visio_service():
    return Mock()

@pytest.fixture
def chatbot_service(mock_ai_service, mock_rag_memory, mock_visio_service):
    config = ChatbotConfig()
    service = ChatbotService(
        config=config,
        ai_service=mock_ai_service,
        rag_memory=mock_rag_memory,
        visio_service=mock_visio_service
    )
    return service

@pytest.mark.asyncio
async def test_handle_general_query_success(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test successful general query handling"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.return_value = "test response"
    
    response = await chatbot_service.handle_general_query("test query")
    
    assert response == "test response"
    mock_rag_memory.query_memory.assert_called_once_with("test query")
    mock_ai_service.generate_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_general_query_retry(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test retry on service error"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.side_effect = [
        ServiceError("Temporary error"),
        ServiceError("Temporary error"),
        "test response"
    ]
    
    response = await chatbot_service.handle_general_query("test query")
    
    assert response == "test response"
    assert mock_ai_service.generate_text.call_count == 3

@pytest.mark.asyncio
async def test_handle_general_query_retry_failure(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test retry exhaustion"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.side_effect = ServiceError("Persistent error")
    
    with pytest.raises(ChatbotError) as exc_info:
        await chatbot_service.handle_general_query("test query")
    
    assert "Failed to process query" in str(exc_info.value)
    assert mock_ai_service.generate_text.call_count == 3

@pytest.mark.asyncio
async def test_handle_general_query_rate_limit(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test retry with rate limit"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.side_effect = [
        RateLimitError("Rate limit", retry_after=0.1),
        "test response"
    ]
    
    response = await chatbot_service.handle_general_query("test query")
    
    assert response == "test response"
    assert mock_ai_service.generate_text.call_count == 2

@pytest.mark.asyncio
async def test_handle_visio_command_success(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test successful Visio command handling"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.return_value = '{"action": "test"}'
    
    response = await chatbot_service.handle_visio_command("test command")
    
    assert response == "Command processed successfully"
    mock_rag_memory.query_memory.assert_called_once_with("test command")
    mock_ai_service.generate_text.assert_called_once()

@pytest.mark.asyncio
async def test_handle_visio_command_retry(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test retry on service error for Visio command"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.side_effect = [
        ServiceError("Temporary error"),
        ServiceError("Temporary error"),
        '{"action": "test"}'
    ]
    
    response = await chatbot_service.handle_visio_command("test command")
    
    assert response == "Command processed successfully"
    assert mock_ai_service.generate_text.call_count == 3

@pytest.mark.asyncio
async def test_handle_visio_command_invalid_json(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test handling of invalid JSON response"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.return_value = "invalid json"
    
    with pytest.raises(ChatbotError) as exc_info:
        await chatbot_service.handle_visio_command("test command")
    
    assert "Failed to parse Visio command interpretation" in str(exc_info.value)

@pytest.mark.asyncio
async def test_conversation_history(chatbot_service, mock_ai_service, mock_rag_memory):
    """Test conversation history management"""
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.return_value = "test response"
    
    # First query
    await chatbot_service.handle_general_query("query 1")
    
    # Second query
    await chatbot_service.handle_general_query("query 2")
    
    # Check conversation history
    history = chatbot_service.conversation_history
    assert len(history) == 4  # 2 queries + 2 responses
    assert history[0]["content"] == "query 1"
    assert history[1]["content"] == "test response"
    assert history[2]["content"] == "query 2"
    assert history[3]["content"] == "test response"

@pytest.mark.asyncio
async def test_performance_logging(chatbot_service, mock_ai_service, mock_rag_memory, tmp_path):
    """Test performance logging"""
    # Configure temp log file
    chatbot_service.config.performance_log = tmp_path / "performance.log"
    
    mock_rag_memory.query_memory.return_value = "test context"
    mock_ai_service.generate_text.return_value = "test response"
    
    await chatbot_service.handle_general_query("test query")
    
    # Check log file
    with open(chatbot_service.config.performance_log) as f:
        log_entry = f.readline()
        assert "test response" in log_entry
        assert "duration" in log_entry
        assert "success" in log_entry 