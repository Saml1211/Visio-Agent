from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseService(ABC):
    """Base class for all services"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        pass

class ServiceUnavailableError(Exception):
    """Raised when a service is unavailable"""
    pass 