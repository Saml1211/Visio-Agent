import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_service import BaseService, ServiceUnavailableError
from .dependency_injector import DependencyInjector
from .ai_services import AIServiceManager
from .gemini_service import GeminiService
from .openai_service import OpenAIService
from .deepseek_service import DeepseekService
from .utils import with_retry
from .exceptions import (
    ServiceError, APIError, RateLimitError,
    AuthenticationError, ServiceExecutionError
)
import httpx

logger = logging.getLogger(__name__)

class LLMOrchestrator(BaseService):
    """Orchestrates multiple LLM services with fallback and retry logic"""
    
    def __init__(self):
        self.dependency_injector = DependencyInjector()
        self.ai_service_manager = AIServiceManager()
        self.services = {
            'gemini': GeminiService(),
            'openai': OpenAIService(),
            'deepseek': DeepseekService()
        }
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Service priority for fallback (ordered by preference)
        self.service_priority = [
            'deepseek',  # Try Deepseek first
            'gemini',    # Then Gemini
            'openai'     # Finally OpenAI
        ]

    async def initialize(self) -> None:
        """Initialize all LLM services"""
        try:
            await self.dependency_injector.initialize()
            for service in self.services.values():
                await service.initialize()
            logger.info("LLM Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Orchestrator: {str(e)}")
            raise ServiceUnavailableError("Failed to initialize services")

    async def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            for service in self.services.values():
                await service.cleanup()
            await self.http_client.aclose()
            logger.info("LLM Orchestrator cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

    @with_retry(
        retries=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(ServiceError, APIError),
        exclude=(AuthenticationError,)
    )
    async def process_request(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        service_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a request using available LLM services with fallback
        
        Args:
            prompt: The prompt to process
            context: Optional context for the request
            service_preference: Optional preferred service to use
            
        Returns:
            Dict containing the response and metadata
            
        Raises:
            ServiceUnavailableError: If no services are available
            ServiceExecutionError: If all services fail
        """
        start_time = time.time()
        
        # Try preferred service first if specified
        if service_preference and service_preference in self.services:
            try:
                service = self.services[service_preference]
                response = await service.process(prompt, context)
                return self._create_response(response, service_preference, start_time)
            except (ServiceError, APIError) as e:
                logger.warning(
                    f"Preferred service {service_preference} failed: {str(e)}"
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error with service {service_preference}: {str(e)}"
                )
                raise ServiceExecutionError(str(e))
        
        # Try services in priority order
        errors = []
        for service_name in self.service_priority:
            if service_name == service_preference:
                continue
                
            try:
                service = self.services[service_name]
                response = await service.process(prompt, context)
                return self._create_response(response, service_name, start_time)
            except RateLimitError as e:
                logger.warning(f"Service {service_name} rate limited: {str(e)}")
                errors.append(f"{service_name}: Rate limit exceeded")
                # Let the retry decorator handle the backoff
                raise
            except AuthenticationError as e:
                logger.error(f"Service {service_name} authentication failed: {str(e)}")
                errors.append(f"{service_name}: Authentication failed")
                continue  # Skip to next service
            except (ServiceError, APIError) as e:
                logger.warning(f"Service {service_name} failed: {str(e)}")
                errors.append(f"{service_name}: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error with service {service_name}: {str(e)}")
                errors.append(f"{service_name}: Unexpected error")
                raise ServiceExecutionError(str(e))
        
        error_msg = "All LLM services failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ServiceUnavailableError(error_msg)

    def _create_response(
        self,
        service_response: Dict[str, Any],
        service_name: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Create a standardized response with metadata"""
        return {
            "response": service_response.get("response"),
            "metadata": {
                "service": service_name,
                "processing_time": time.time() - start_time,
                "timestamp": datetime.utcnow().isoformat(),
                "service_metadata": service_response.get("metadata", {})
            }
        }

    async def get_service_status(self) -> Dict[str, str]:
        """Get status of all services"""
        status = {}
        for name, service in self.services.items():
            try:
                await service.health_check()
                status[name] = "available"
            except Exception as e:
                logger.warning(f"Service {name} health check failed: {str(e)}")
                status[name] = "unavailable"
        return status 