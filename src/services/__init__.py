from .service_registry import ServiceRegistry

def register_services():
    """Register all available services with the registry"""
    registry = ServiceRegistry()
    return registry 