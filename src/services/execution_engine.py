import platform
import logging
from typing import Optional, Dict, Any
from .service_registry import ServiceRegistry
from .visio.windows_visio_service import WindowsVisioService
from .visio.mac_diagram_service import MacDiagramService

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self):
        self.os_type = platform.system()
        self.registry = ServiceRegistry()
        
    async def run_service(self, service_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if service_name == "diagramGeneration":
                service = self._get_diagram_service()
            else:
                service_class = self.registry.get(service_name)
                if not service_class:
                    raise ValueError(f"Service not found: {service_name}")
                service = service_class()
                
            return await service.execute(input_data)
            
        except Exception as e:
            logger.error(f"Service execution failed: {str(e)}")
            raise
            
    def _get_diagram_service(self) -> BaseService:
        """Get the appropriate diagram service for the current platform"""
        if self.os_type == "Windows":
            try:
                return WindowsVisioService()
            except RuntimeError:
                logger.warning("Falling back to browser-based diagram service on Windows")
                return MacDiagramService()
        return MacDiagramService() 