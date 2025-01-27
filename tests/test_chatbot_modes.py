import pytest
from unittest.mock import AsyncMock
from src.services.chatbot import EnhancedChatbot, ChatbotMode

@pytest.fixture
def mock_services():
    return {
        "rag": AsyncMock(),
        "learning": AsyncMock()
    }

@pytest.mark.asyncio
async def test_mode_switching(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    
    # Test initial mode
    assert chatbot.mode == ChatbotMode.CHAT
    
    # Test switching to Action Mode
    response = await chatbot.handle_message("user1", "/mode action")
    assert "Action Mode" in response
    assert chatbot.mode == ChatbotMode.ACTION
    
    # Test switching to Chat Mode
    response = await chatbot.handle_message("user1", "/mode chat")
    assert "Chat Mode" in response
    assert chatbot.mode == ChatbotMode.CHAT

@pytest.mark.asyncio
async def test_action_mode(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    await chatbot.handle_message("user1", "/mode action")
    
    response = await chatbot.handle_message("user1", "generate report")
    assert "Executed action" in response
    assert len(chatbot.conversation_history) == 1
    assert chatbot.conversation_history[0]["type"] == "action"

@pytest.mark.asyncio
async def test_chat_mode(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    await chatbot.handle_message("user1", "/mode chat")
    
    response = await chatbot.handle_message("user1", "What is HDMI?")
    assert "HDMI" in response
    assert len(chatbot.conversation_history) == 1
    assert chatbot.conversation_history[0]["type"] == "chat"

@pytest.mark.asyncio
async def test_auto_mode_switching(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    
    # Test action command detection
    await chatbot.handle_message("user1", "generate report")
    assert chatbot.mode == ChatbotMode.ACTION
    
    # Test question detection
    await chatbot.handle_message("user1", "What is HDMI?")
    assert chatbot.mode == ChatbotMode.CHAT

@pytest.mark.asyncio
async def test_help_command(mock_services):
    chatbot = EnhancedChatbot(mock_services["rag"], mock_services["learning"])
    
    # Test action mode help
    await chatbot.handle_message("user1", "/mode action")
    response = await chatbot.handle_message("user1", "/help")
    assert "Action Mode Help" in response
    
    # Test chat mode help
    await chatbot.handle_message("user1", "/mode chat")
    response = await chatbot.handle_message("user1", "/help")
    assert "Chat Mode Help" in response 