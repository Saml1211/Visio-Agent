from typing import Dict, Any, Type
import logging
from .base_service import BaseService

logger = logging.getLogger(__name__)

class DependencyInjector:
    """Manages service dependencies and initialization"""
    
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all registered services"""
        if self._initialized:
            return
            
        for service in self._services.values():
            await service.initialize()
        self._initialized = True

    def register(self, name: str, service: BaseService) -> None:
        """Register a service"""
        if name in self._services:
            logger.warning(f"Service {name} already registered, replacing")
        self._services[name] = service

    def get(self, name: str) -> BaseService:
        """Get a registered service"""
        if name not in self._services:
            raise KeyError(f"Service {name} not registered")
        return self._services[name] 