from .service_registry import ServiceRegistry, ComponentExtractor, SpecsFetcher
from .visio.windows_visio_service import WindowsVisioService
from .visio.mac_diagram_service import MacDiagramService
from .visio_generation_service import VisioGenerationService
from .connector_routing import ConnectorRouter
from .exceptions import (
    VisioGenerationError,
    VisioRoutingError,
    ValidationError,
    ServiceError
)

def register_services():
    """Register all available services with the registry"""
    registry = ServiceRegistry()
    registry.register("componentExtractor", ComponentExtractor)
    registry.register("specsFetcher", SpecsFetcher)
    registry.register("diagramGeneration", 
                     WindowsVisioService if platform.system() == "Windows" 
                     else MacDiagramService) 