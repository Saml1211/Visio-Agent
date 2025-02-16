class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass

class ValidationError(Exception):
    """Base exception for validation errors."""
    pass

class ConfigurationError(Exception):
    """Base exception for configuration errors."""
    pass 