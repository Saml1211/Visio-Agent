import pytest
from unittest.mock import AsyncMock
from src.services.chatbot import EnhancedChatbot

@pytest.fixture
def mock_services():
    return {
        "rag": AsyncMock(),
        "learning": AsyncMock()
    }

@pytest.mark.asyncio
async def test_store_command(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    response = await chatbot.handle_message("user1", "/store test content")
    assert "successfully stored" in response
    mock_services["rag"].store_memory.assert_called_once()

@pytest.mark.asyncio
async def test_fine_tune_command(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    # Add conversation history
    await chatbot.handle_message("user1", "test message")
    response = await chatbot.handle_message("user1", "/fine-tune")
    assert "initiated successfully" in response
    mock_services["learning"].fine_tune_model.assert_called_once()

@pytest.mark.asyncio
async def test_rag_command(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    mock_services["rag"].query_memory.return_value = [{"content": "test result"}]
    response = await chatbot.handle_message("user1", "/rag test query")
    assert "test result" in response
    mock_services["rag"].query_memory.assert_called_once_with("test query") 