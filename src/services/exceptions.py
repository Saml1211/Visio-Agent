"""Custom exceptions for the chatbot application"""

class ChatbotError(Exception):
    """Base exception for all chatbot-related errors"""
    pass

class ServiceError(ChatbotError):
    """Base exception for service-related errors"""
    pass

class ConfigurationError(ChatbotError):
    """Error related to configuration loading or validation"""
    pass

class AIServiceError(ServiceError):
    """Error related to AI service operations"""
    pass

class RAGMemoryError(ServiceError):
    """Error related to RAG memory operations"""
    pass

class VisioServiceError(ServiceError):
    """Error related to Visio service operations"""
    pass

class UIError(ChatbotError):
    """Error related to UI operations"""
    pass

class HotkeyError(ChatbotError):
    """Error related to hotkey operations"""
    pass

class ThreadingError(ChatbotError):
    """Error related to threading operations"""
    pass

class ValidationError(ChatbotError):
    """Error related to data validation"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message)
        self.field = field

class APIError(ServiceError):
    """Error related to external API calls"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code

class RateLimitError(APIError):
    """Error related to API rate limiting"""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after

class AuthenticationError(APIError):
    """Error related to API authentication"""
    pass

class ResourceNotFoundError(ServiceError):
    """Error when a requested resource is not found"""
    def __init__(self, message: str, resource_type: str = None):
        super().__init__(message)
        self.resource_type = resource_type

class StateError(ChatbotError):
    """Error related to invalid state transitions"""
    def __init__(self, message: str, current_state: str = None, target_state: str = None):
        super().__init__(message)
        self.current_state = current_state
        self.target_state = target_state

class MemoryError(ServiceError):
    """Error related to memory management"""
    def __init__(self, message: str, memory_type: str = None):
        super().__init__(message)
        self.memory_type = memory_type

class PerformanceError(ServiceError):
    """Error related to performance issues"""
    def __init__(self, message: str, threshold: float = None, actual: float = None):
        super().__init__(message)
        self.threshold = threshold
        self.actual = actual

class SecurityError(ChatbotError):
    """Error related to security violations"""
    def __init__(self, message: str, violation_type: str = None):
        super().__init__(message)
        self.violation_type = violation_type

class ProcessingError(Exception):
    """Raised when file processing fails"""
    pass

class CacheError(Exception):
    """Raised when cache operations fail"""
    pass

class VisioError(Exception):
    """Raised when Visio operations fail"""
    pass 