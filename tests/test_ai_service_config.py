import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import json
from pathlib import Path
import tempfile
import aiohttp
import asyncio
import numpy as np
import torch
from PIL import Image
import io

from src.services.ai_service_config import (
    AIServiceManager,
    AIServiceType,
    TaskType,
    ModelConfig,
    ServiceConfig,
    OpenAIProvider,
    HuggingFaceProvider,
    AIServiceError
)

@pytest.fixture
def test_config():
    return {
        "openai_service": {
            "service_type": "openai",
            "api_key": "test_key",
            "api_base": "https://api.openai.com/v1",
            "organization_id": "test_org",
            "timeout": 30.0,
            "max_retries": 3,
            "retry_delay": 1.0,
            "models": {
                "text_generation": {
                    "model_id": "gpt-4",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0
                },
                "text_embedding": {
                    "model_id": "text-embedding-ada-002"
                },
                "image_analysis": {
                    "model_id": "gpt-4-vision-preview",
                    "max_tokens": 500,
                    "temperature": 0.5
                }
            }
        },
        "huggingface_service": {
            "service_type": "huggingface",
            "api_key": "test_key",
            "timeout": 30.0,
            "max_retries": 3,
            "retry_delay": 1.0,
            "models": {
                "text_generation": {
                    "model_id": "gpt2",
                    "max_tokens": 1000,
                    "temperature": 0.7,
                    "top_p": 0.9
                },
                "text_embedding": {
                    "model_id": "sentence-transformers/all-MiniLM-L6-v2"
                },
                "image_analysis": {
                    "model_id": "Salesforce/blip-image-captioning-base",
                    "max_tokens": 500,
                    "temperature": 0.5
                }
            }
        }
    }

@pytest.fixture
def config_file(tmp_path, test_config):
    config_path = tmp_path / "ai_services.json"
    with open(config_path, "w") as f:
        json.dump(test_config, f)
    return config_path

@pytest.fixture
def mock_openai():
    with patch("openai.AsyncOpenAI") as mock:
        client = AsyncMock()
        
        # Mock chat completions
        chat_completion = AsyncMock()
        chat_completion.choices = [
            MagicMock(message=MagicMock(content="Test response"))
        ]
        client.chat.completions.create = AsyncMock(
            return_value=chat_completion
        )
        
        # Mock embeddings
        embedding = AsyncMock()
        embedding.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        client.embeddings.create = AsyncMock(return_value=embedding)
        
        mock.return_value = client
        yield mock

@pytest.fixture
def mock_huggingface():
    with patch("transformers.AutoTokenizer") as mock_tokenizer:
        with patch("transformers.AutoModel") as mock_model:
            tokenizer = MagicMock()
            tokenizer.return_value = MagicMock()
            mock_tokenizer.from_pretrained.return_value = tokenizer
            
            model = MagicMock()
            model.generate.return_value = torch.tensor([[1, 2, 3]])
            model.return_value = model
            mock_model.from_pretrained.return_value = model
            
            yield mock_tokenizer, mock_model

@pytest.mark.asyncio
async def test_openai_provider_initialization(test_config):
    # Create provider
    config = ServiceConfig(**test_config["openai_service"])
    provider = OpenAIProvider(config)
    
    assert provider.config == config
    assert provider.client is not None

@pytest.mark.asyncio
async def test_openai_text_generation(mock_openai, test_config):
    # Create provider
    config = ServiceConfig(**test_config["openai_service"])
    provider = OpenAIProvider(config)
    
    # Generate text
    response = await provider.generate_text(
        "Test prompt",
        task_type=TaskType.TEXT_GENERATION
    )
    
    assert response == "Test response"
    provider.client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_openai_embedding_generation(mock_openai, test_config):
    # Create provider
    config = ServiceConfig(**test_config["openai_service"])
    provider = OpenAIProvider(config)
    
    # Generate embedding
    embedding = await provider.generate_embedding("Test text")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 3
    provider.client.embeddings.create.assert_called_once()

@pytest.mark.asyncio
async def test_openai_image_analysis(mock_openai, test_config):
    # Create provider
    config = ServiceConfig(**test_config["openai_service"])
    provider = OpenAIProvider(config)
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    
    # Analyze image
    response = await provider.analyze_image(
        img_bytes.getvalue(),
        prompt="Describe this image"
    )
    
    assert response == "Test response"
    provider.client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_huggingface_provider_initialization(test_config, mock_huggingface):
    # Create provider
    config = ServiceConfig(**test_config["huggingface_service"])
    provider = HuggingFaceProvider(config)
    
    assert provider.config == config
    assert provider.client is not None

@pytest.mark.asyncio
async def test_huggingface_text_generation(test_config, mock_huggingface):
    # Create provider
    config = ServiceConfig(**test_config["huggingface_service"])
    provider = HuggingFaceProvider(config)
    
    # Generate text
    response = await provider.generate_text(
        "Test prompt",
        task_type=TaskType.TEXT_GENERATION
    )
    
    assert response is not None
    mock_huggingface[0].from_pretrained.assert_called_once()
    mock_huggingface[1].from_pretrained.assert_called_once()

@pytest.mark.asyncio
async def test_huggingface_embedding_generation(test_config, mock_huggingface):
    # Create provider
    config = ServiceConfig(**test_config["huggingface_service"])
    provider = HuggingFaceProvider(config)
    
    # Generate embedding
    embedding = await provider.generate_embedding("Test text")
    
    assert isinstance(embedding, list)
    mock_huggingface[0].from_pretrained.assert_called_once()
    mock_huggingface[1].from_pretrained.assert_called_once()

@pytest.mark.asyncio
async def test_huggingface_image_analysis(test_config, mock_huggingface):
    # Create provider
    config = ServiceConfig(**test_config["huggingface_service"])
    provider = HuggingFaceProvider(config)
    
    # Create test image
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    
    # Analyze image
    response = await provider.analyze_image(
        img_bytes.getvalue(),
        prompt="Describe this image"
    )
    
    assert response is not None
    mock_huggingface[0].from_pretrained.assert_called_once()
    mock_huggingface[1].from_pretrained.assert_called_once()

@pytest.mark.asyncio
async def test_service_manager_initialization(config_file):
    # Create manager
    manager = AIServiceManager(config_file)
    
    assert len(manager.providers) == 2
    assert "openai_service" in manager.providers
    assert "huggingface_service" in manager.providers

@pytest.mark.asyncio
async def test_service_manager_get_provider(config_file):
    # Create manager
    manager = AIServiceManager(config_file)
    
    # Get specific provider
    provider = manager.get_provider("openai_service")
    assert isinstance(provider, OpenAIProvider)
    
    # Get default provider
    provider = manager.get_provider()
    assert isinstance(provider, (OpenAIProvider, HuggingFaceProvider))

@pytest.mark.asyncio
async def test_service_manager_register_provider(config_file):
    # Create manager
    manager = AIServiceManager(config_file)
    
    # Create new provider
    config = ServiceConfig(**{
        "service_type": "openai",
        "api_key": "test_key",
        "models": {}
    })
    provider = OpenAIProvider(config)
    
    # Register provider
    manager.register_provider("new_provider", provider)
    
    assert "new_provider" in manager.providers
    assert manager.providers["new_provider"] == provider

@pytest.mark.asyncio
async def test_service_manager_remove_provider(config_file):
    # Create manager
    manager = AIServiceManager(config_file)
    
    # Remove provider
    manager.remove_provider("openai_service")
    
    assert "openai_service" not in manager.providers

@pytest.mark.asyncio
async def test_error_handling():
    # Test invalid service type
    with pytest.raises(AIServiceError):
        config = ServiceConfig(**{
            "service_type": "invalid",
            "api_key": "test_key",
            "models": {}
        })
    
    # Test missing model configuration
    config = ServiceConfig(**{
        "service_type": "openai",
        "api_key": "test_key",
        "models": {}
    })
    provider = OpenAIProvider(config)
    
    with pytest.raises(AIServiceError):
        await provider.generate_text(
            "Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
    
    # Test provider not found
    manager = AIServiceManager()
    with pytest.raises(AIServiceError):
        manager.get_provider("nonexistent")
    
    # Test duplicate provider registration
    config = ServiceConfig(**{
        "service_type": "openai",
        "api_key": "test_key",
        "models": {}
    })
    provider = OpenAIProvider(config)
    
    manager.register_provider("test", provider)
    with pytest.raises(AIServiceError):
        manager.register_provider("test", provider)

@pytest.mark.asyncio
async def test_retry_mechanism(mock_openai, test_config):
    # Configure mock to fail twice then succeed
    mock_openai.return_value.chat.completions.create.side_effect = [
        Exception("First failure"),
        Exception("Second failure"),
        AsyncMock(
            choices=[MagicMock(message=MagicMock(content="Success"))]
        )
    ]
    
    # Create provider
    config = ServiceConfig(**test_config["openai_service"])
    provider = OpenAIProvider(config)
    
    # Generate text
    response = await provider.generate_text(
        "Test prompt",
        task_type=TaskType.TEXT_GENERATION
    )
    
    assert response == "Success"
    assert mock_openai.return_value.chat.completions.create.call_count == 3

@pytest.mark.asyncio
async def test_timeout_handling(mock_openai, test_config):
    # Configure mock to timeout
    async def timeout_side_effect(*args, **kwargs):
        await asyncio.sleep(2)
        return AsyncMock(
            choices=[MagicMock(message=MagicMock(content="Too late"))]
        )
    
    mock_openai.return_value.chat.completions.create.side_effect = timeout_side_effect
    
    # Create provider with short timeout
    config = ServiceConfig(**{
        **test_config["openai_service"],
        "timeout": 0.1
    })
    provider = OpenAIProvider(config)
    
    # Generate text
    with pytest.raises(AIServiceError) as exc_info:
        await provider.generate_text(
            "Test prompt",
            task_type=TaskType.TEXT_GENERATION
        )
    
    assert "timed out" in str(exc_info.value).lower() 