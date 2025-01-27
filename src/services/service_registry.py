from typing import Dict, Type, Optional
from abc import ABC, abstractmethod
import logging
from .tech_specs_service import TechSpecsService
from .data_ingestion import FirecrawlService
import platform
from datetime import datetime
from .exceptions import ServiceNotFoundError, ServiceExecutionError
from .ai_services.vertex_ai_service import VertexAIService

logger = logging.getLogger(__name__)

class BaseService(ABC):
    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """Execute the service with given input data"""
        pass

class ServiceRegistry:
    _instance: Optional['ServiceRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.services = {
                "openai": OpenAIService,
                "vertexai": VertexAIService,
                "huggingface": HuggingFaceService
            }
        return cls._instance
    
    def register(self, name: str, service: Type[BaseService]) -> None:
        """Register a service with the registry"""
        self.services[name] = service
        logger.info(f"Registered service: {name}")
        
    def get(self, name: str) -> Optional[Type[BaseService]]:
        """Get a service by name"""
        service = self.services.get(name)
        if not service:
            logger.warning(f"Service not found: {name}")
        return service

    async def shutdown(self):
        """Gracefully shutdown all active services"""
        for service_name, service_class in self.services.items():
            try:
                if hasattr(service_class, 'shutdown'):
                    await service_class.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down {service_name}: {str(e)}")

# Platform-agnostic base services
class ComponentExtractor(BaseService):
    async def execute(self, input_data: dict) -> dict:
        try:
            tech_specs = TechSpecsService()
            return await tech_specs.extract_components(input_data["text"])
        except Exception as e:
            logger.error(f"Component extraction failed: {str(e)}")
            raise

class SpecsFetcher(BaseService):
    async def execute(self, input_data: dict) -> dict:
        try:
            firecrawl = FirecrawlService()
            return await firecrawl.scrape_url(input_data["model_url"])
        except Exception as e:
            logger.error(f"Specs fetching failed: {str(e)}")
            raise 