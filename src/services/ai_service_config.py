import logging
from typing import Dict, List, Optional, Any, Protocol, Union
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import aiofiles
from .exceptions import ConfigurationError
import aiohttp
import asyncio
from datetime import datetime
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
import os

logger = logging.getLogger(__name__)

class AIServiceType(str, Enum):
    """Types of AI services supported"""
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    AZURE = "azure"

class TaskType(str, Enum):
    """Types of tasks supported"""
    TEXT_GENERATION = "text_generation"
    TEXT_EMBEDDING = "text_embedding"
    IMAGE_ANALYSIS = "image_analysis"
    IMAGE_EMBEDDING = "image_embedding"
    CODE_GENERATION = "code_generation"
    DIAGRAM_VALIDATION = "diagram_validation"

@dataclass
class ModelConfig:
    """Configuration for an AI model"""
    model_id: str
    task_type: TaskType
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    custom_parameters: Optional[Dict[str, Any]] = None

@dataclass
class ServiceConfig:
    """Configuration for an AI service"""
    service_type: AIServiceType
    api_key: str
    api_base: Optional[str] = None
    organization_id: Optional[str] = None
    models: Dict[TaskType, ModelConfig] = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0

class AIServiceError(Exception):
    """Base exception for AI service errors"""
    pass

class OpenAIProvider:
    """OpenAI service provider implementation"""
    
    def __init__(self, config: ServiceConfig):
        """Initialize OpenAI provider
        
        Args:
            config: Service configuration
        """
        import openai
        
        self.config = config
        openai.api_key = config.api_key
        
        if config.api_base:
            openai.api_base = config.api_base
        if config.organization_id:
            openai.organization = config.organization_id
        
        self.client = openai.AsyncOpenAI()
        logger.info(f"Initialized OpenAI provider with {len(config.models)} models")
    
    async def generate_text(
        self,
        prompt: str,
        task_type: TaskType = TaskType.TEXT_GENERATION,
        **kwargs
    ) -> str:
        """Generate text using OpenAI
        
        Args:
            prompt: Input prompt
            task_type: Type of task
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        try:
            model_config = self.config.models.get(task_type)
            if not model_config:
                raise AIServiceError(f"No model configured for task: {task_type}")
            
            # Prepare parameters
            params = {
                "model": model_config.model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": model_config.max_tokens,
                "temperature": model_config.temperature,
                "top_p": model_config.top_p,
                "frequency_penalty": model_config.frequency_penalty,
                "presence_penalty": model_config.presence_penalty,
                "stop": model_config.stop_sequences,
                **kwargs
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Generate text with retries
            for attempt in range(self.config.max_retries):
                try:
                    async with asyncio.timeout(self.config.timeout):
                        response = await self.client.chat.completions.create(**params)
                        return response.choices[0].message.content
                        
                except asyncio.TimeoutError:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError("OpenAI request timed out")
                    await asyncio.sleep(self.config.retry_delay)
                    
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError(f"OpenAI error: {str(e)}")
                    await asyncio.sleep(self.config.retry_delay)
            
        except Exception as e:
            logger.error(f"Error generating text with OpenAI: {str(e)}")
            raise AIServiceError(f"Failed to generate text: {str(e)}")
    
    async def generate_embedding(
        self,
        text: Union[str, bytes],
        model: Optional[str] = None,
        **kwargs
    ) -> List[float]:
        """Generate embedding using OpenAI
        
        Args:
            text: Input text or image data
            model: Optional model override
            **kwargs: Additional parameters
            
        Returns:
            Embedding vector
        """
        try:
            task_type = (
                TaskType.IMAGE_EMBEDDING if isinstance(text, bytes)
                else TaskType.TEXT_EMBEDDING
            )
            
            model_config = self.config.models.get(task_type)
            if not model_config:
                raise AIServiceError(f"No model configured for task: {task_type}")
            
            # Use specified model or default
            model_id = model or model_config.model_id
            
            # Generate embedding with retries
            for attempt in range(self.config.max_retries):
                try:
                    async with asyncio.timeout(self.config.timeout):
                        response = await self.client.embeddings.create(
                            model=model_id,
                            input=text if isinstance(text, str) else base64.b64encode(text).decode(),
                            **kwargs
                        )
                        return response.data[0].embedding
                        
                except asyncio.TimeoutError:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError("OpenAI request timed out")
                    await asyncio.sleep(self.config.retry_delay)
                    
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError(f"OpenAI error: {str(e)}")
                    await asyncio.sleep(self.config.retry_delay)
            
        except Exception as e:
            logger.error(f"Error generating embedding with OpenAI: {str(e)}")
            raise AIServiceError(f"Failed to generate embedding: {str(e)}")
    
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Analyze image using OpenAI
        
        Args:
            image_data: Image data
            prompt: Optional prompt for analysis
            **kwargs: Additional parameters
            
        Returns:
            Analysis text
        """
        try:
            model_config = self.config.models.get(TaskType.IMAGE_ANALYSIS)
            if not model_config:
                raise AIServiceError("No model configured for image analysis")
            
            # Encode image
            image_b64 = base64.b64encode(image_data).decode()
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image_url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    ]
                }
            ]
            
            if prompt:
                messages[0]["content"].append({
                    "type": "text",
                    "text": prompt
                })
            
            # Analyze image with retries
            for attempt in range(self.config.max_retries):
                try:
                    async with asyncio.timeout(self.config.timeout):
                        response = await self.client.chat.completions.create(
                            model=model_config.model_id,
                            messages=messages,
                            max_tokens=model_config.max_tokens,
                            temperature=model_config.temperature,
                            **kwargs
                        )
                        return response.choices[0].message.content
                        
                except asyncio.TimeoutError:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError("OpenAI request timed out")
                    await asyncio.sleep(self.config.retry_delay)
                    
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError(f"OpenAI error: {str(e)}")
                    await asyncio.sleep(self.config.retry_delay)
            
        except Exception as e:
            logger.error(f"Error analyzing image with OpenAI: {str(e)}")
            raise AIServiceError(f"Failed to analyze image: {str(e)}")

class HuggingFaceProvider:
    """Hugging Face service provider implementation"""
    
    def __init__(self, config: ServiceConfig):
        """Initialize Hugging Face provider
        
        Args:
            config: Service configuration
        """
        self.config = config
        self.client = None
        self.tokenizers = {}
        self.models = {}
        
        # Initialize client
        from huggingface_hub import HfApi
        self.client = HfApi(token=config.api_key)
        
        logger.info(f"Initialized Hugging Face provider with {len(config.models)} models")
    
    async def _load_model(self, model_id: str) -> None:
        """Load model and tokenizer
        
        Args:
            model_id: Model identifier
        """
        try:
            if model_id not in self.models:
                self.tokenizers[model_id] = AutoTokenizer.from_pretrained(model_id)
                self.models[model_id] = AutoModel.from_pretrained(model_id)
                
        except Exception as e:
            logger.error(f"Error loading model {model_id}: {str(e)}")
            raise AIServiceError(f"Failed to load model: {str(e)}")
    
    async def generate_text(
        self,
        prompt: str,
        task_type: TaskType = TaskType.TEXT_GENERATION,
        **kwargs
    ) -> str:
        """Generate text using Hugging Face
        
        Args:
            prompt: Input prompt
            task_type: Type of task
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        try:
            model_config = self.config.models.get(task_type)
            if not model_config:
                raise AIServiceError(f"No model configured for task: {task_type}")
            
            # Load model if needed
            await self._load_model(model_config.model_id)
            
            # Prepare parameters
            params = {
                "max_length": model_config.max_tokens,
                "temperature": model_config.temperature,
                "top_p": model_config.top_p,
                "repetition_penalty": model_config.frequency_penalty,
                "stop_sequences": model_config.stop_sequences,
                **kwargs
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Generate text with retries
            for attempt in range(self.config.max_retries):
                try:
                    async with asyncio.timeout(self.config.timeout):
                        # Tokenize input
                        inputs = self.tokenizers[model_config.model_id](
                            prompt,
                            return_tensors="pt",
                            padding=True,
                            truncation=True
                        )
                        
                        # Generate
                        outputs = self.models[model_config.model_id].generate(
                            **inputs,
                            **params
                        )
                        
                        # Decode output
                        return self.tokenizers[model_config.model_id].decode(
                            outputs[0],
                            skip_special_tokens=True
                        )
                        
                except asyncio.TimeoutError:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError("Hugging Face request timed out")
                    await asyncio.sleep(self.config.retry_delay)
                    
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError(f"Hugging Face error: {str(e)}")
                    await asyncio.sleep(self.config.retry_delay)
            
        except Exception as e:
            logger.error(f"Error generating text with Hugging Face: {str(e)}")
            raise AIServiceError(f"Failed to generate text: {str(e)}")
    
    async def generate_embedding(
        self,
        text: Union[str, bytes],
        model: Optional[str] = None,
        **kwargs
    ) -> List[float]:
        """Generate embedding using Hugging Face
        
        Args:
            text: Input text or image data
            model: Optional model override
            **kwargs: Additional parameters
            
        Returns:
            Embedding vector
        """
        try:
            task_type = (
                TaskType.IMAGE_EMBEDDING if isinstance(text, bytes)
                else TaskType.TEXT_EMBEDDING
            )
            
            model_config = self.config.models.get(task_type)
            if not model_config:
                raise AIServiceError(f"No model configured for task: {task_type}")
            
            # Use specified model or default
            model_id = model or model_config.model_id
            
            # Load model if needed
            await self._load_model(model_id)
            
            # Generate embedding with retries
            for attempt in range(self.config.max_retries):
                try:
                    async with asyncio.timeout(self.config.timeout):
                        if isinstance(text, str):
                            # Text embedding
                            inputs = self.tokenizers[model_id](
                                text,
                                return_tensors="pt",
                                padding=True,
                                truncation=True
                            )
                            
                            with torch.no_grad():
                                outputs = self.models[model_id](**inputs)
                                
                            # Use CLS token embedding
                            embedding = outputs.last_hidden_state[:, 0].numpy()
                            return embedding[0].tolist()
                            
                        else:
                            # Image embedding
                            from PIL import Image
                            import io
                            
                            # Load image
                            image = Image.open(io.BytesIO(text))
                            
                            # Process image
                            processor = self.tokenizers[model_id]
                            inputs = processor(image, return_tensors="pt")
                            
                            with torch.no_grad():
                                outputs = self.models[model_id](**inputs)
                                
                            # Use image embedding
                            embedding = outputs.image_embeds.numpy()
                            return embedding[0].tolist()
                        
                except asyncio.TimeoutError:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError("Hugging Face request timed out")
                    await asyncio.sleep(self.config.retry_delay)
                    
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError(f"Hugging Face error: {str(e)}")
                    await asyncio.sleep(self.config.retry_delay)
            
        except Exception as e:
            logger.error(f"Error generating embedding with Hugging Face: {str(e)}")
            raise AIServiceError(f"Failed to generate embedding: {str(e)}")
    
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Analyze image using Hugging Face
        
        Args:
            image_data: Image data
            prompt: Optional prompt for analysis
            **kwargs: Additional parameters
            
        Returns:
            Analysis text
        """
        try:
            model_config = self.config.models.get(TaskType.IMAGE_ANALYSIS)
            if not model_config:
                raise AIServiceError("No model configured for image analysis")
            
            # Load model if needed
            await self._load_model(model_config.model_id)
            
            # Analyze image with retries
            for attempt in range(self.config.max_retries):
                try:
                    async with asyncio.timeout(self.config.timeout):
                        from PIL import Image
                        import io
                        
                        # Load image
                        image = Image.open(io.BytesIO(image_data))
                        
                        # Process image and prompt
                        processor = self.tokenizers[model_config.model_id]
                        if prompt:
                            inputs = processor(
                                images=image,
                                text=prompt,
                                return_tensors="pt"
                            )
                        else:
                            inputs = processor(
                                images=image,
                                return_tensors="pt"
                            )
                        
                        # Generate analysis
                        outputs = self.models[model_config.model_id].generate(
                            **inputs,
                            max_length=model_config.max_tokens,
                            temperature=model_config.temperature
                        )
                        
                        # Decode output
                        return processor.decode(
                            outputs[0],
                            skip_special_tokens=True
                        )
                        
                except asyncio.TimeoutError:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError("Hugging Face request timed out")
                    await asyncio.sleep(self.config.retry_delay)
                    
                except Exception as e:
                    if attempt == self.config.max_retries - 1:
                        raise AIServiceError(f"Hugging Face error: {str(e)}")
                    await asyncio.sleep(self.config.retry_delay)
            
        except Exception as e:
            logger.error(f"Error analyzing image with Hugging Face: {str(e)}")
            raise AIServiceError(f"Failed to analyze image: {str(e)}")

class AIServiceManager:
    """Manager for AI services"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize AI service manager
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or Path("config/ai_services.json")
        self.providers = {}
        self._load_config()
        
        logger.info(f"Initialized AI service manager with {len(self.providers)} providers")
    
    def _load_config(self) -> None:
        """Load service configurations"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}")
                return
            
            with open(self.config_path) as f:
                config_data = json.load(f)
            
            for service_name, service_config in config_data.items():
                # Create service config
                config = ServiceConfig(
                    service_type=AIServiceType(service_config["service_type"]),
                    api_key=service_config["api_key"],
                    api_base=service_config.get("api_base"),
                    organization_id=service_config.get("organization_id"),
                    timeout=service_config.get("timeout", 30.0),
                    max_retries=service_config.get("max_retries", 3),
                    retry_delay=service_config.get("retry_delay", 1.0)
                )
                
                # Create model configs
                config.models = {}
                for task_name, model_config in service_config["models"].items():
                    config.models[TaskType(task_name)] = ModelConfig(
                        model_id=model_config["model_id"],
                        task_type=TaskType(task_name),
                        max_tokens=model_config.get("max_tokens"),
                        temperature=model_config.get("temperature"),
                        top_p=model_config.get("top_p"),
                        frequency_penalty=model_config.get("frequency_penalty"),
                        presence_penalty=model_config.get("presence_penalty"),
                        stop_sequences=model_config.get("stop_sequences"),
                        custom_parameters=model_config.get("custom_parameters")
                    )
                
                # Create provider
                if config.service_type == AIServiceType.OPENAI:
                    self.providers[service_name] = OpenAIProvider(config)
                elif config.service_type == AIServiceType.HUGGINGFACE:
                    self.providers[service_name] = HuggingFaceProvider(config)
                else:
                    logger.warning(f"Unsupported service type: {config.service_type}")
            
        except Exception as e:
            logger.error(f"Error loading AI service config: {str(e)}")
            raise AIServiceError(f"Failed to load config: {str(e)}")
    
    def get_provider(self, name: Optional[str] = None) -> Union[OpenAIProvider, HuggingFaceProvider]:
        """Get an AI service provider
        
        Args:
            name: Provider name (uses first available if not specified)
            
        Returns:
            AI service provider
            
        Raises:
            AIServiceError: If no provider is available
        """
        try:
            if not self.providers:
                raise AIServiceError("No AI service providers configured")
            
            if name:
                if name not in self.providers:
                    raise AIServiceError(f"Provider not found: {name}")
                return self.providers[name]
            
            # Return first available provider
            return next(iter(self.providers.values()))
            
        except Exception as e:
            logger.error(f"Error getting AI service provider: {str(e)}")
            raise AIServiceError(f"Failed to get provider: {str(e)}")
    
    def register_provider(
        self,
        name: str,
        provider: Union[OpenAIProvider, HuggingFaceProvider]
    ) -> None:
        """Register a new AI service provider
        
        Args:
            name: Provider name
            provider: Provider instance
            
        Raises:
            AIServiceError: If provider already exists
        """
        try:
            if name in self.providers:
                raise AIServiceError(f"Provider already exists: {name}")
            
            self.providers[name] = provider
            logger.info(f"Registered new AI service provider: {name}")
            
        except Exception as e:
            logger.error(f"Error registering AI service provider: {str(e)}")
            raise AIServiceError(f"Failed to register provider: {str(e)}")
    
    def remove_provider(self, name: str) -> None:
        """Remove an AI service provider
        
        Args:
            name: Provider name
            
        Raises:
            AIServiceError: If provider not found
        """
        try:
            if name not in self.providers:
                raise AIServiceError(f"Provider not found: {name}")
            
            del self.providers[name]
            logger.info(f"Removed AI service provider: {name}")
            
        except Exception as e:
            logger.error(f"Error removing AI service provider: {str(e)}")
            raise AIServiceError(f"Failed to remove provider: {str(e)}")

class AIServiceConfig:
    def __init__(self):
        self.providers = {
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model_map": {
                    "analyze_content": "gpt-4-turbo",
                    "text_generation": "gpt-4"
                }
            },
            "vertexai": {
                "project_id": os.getenv("VERTEXAI_PROJECT_ID"),
                "location": os.getenv("VERTEXAI_LOCATION", "us-central1"),
                "model_map": {
                    "analyze_content": "gemini-1.5-pro",
                    "text_generation": "gemini-pro"
                }
            }
        }
        self.default_provider = "vertexai" if os.getenv("VERTEXAI_PROJECT_ID") else "openai"

# Limitations:
# 1. No versioning/rollback support for prompt changes
# 2. No support for prompt templates with complex logic/conditionals
# 3. No built-in validation for prompt length/token limits
# 4. Basic latency tracking (simple rolling average)
# 5. No support for A/B testing different prompts
# 6. Limited prompt testing capabilities (no actual AI calls)
# 7. No support for prompt chaining or dependencies
# 8. Simple file-based storage (may not scale well) 