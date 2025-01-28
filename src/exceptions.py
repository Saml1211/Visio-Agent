"""
Custom exceptions for the LLD Automation Project.
"""

from typing import Optional, Dict, Any

class ValidationError(Exception):
    """Exception raised for validation errors in the LLD Automation Project.
    
    Attributes:
        message -- explanation of the error
        code -- error code for categorization
        details -- additional error details
        context -- contextual information about where the error occurred
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or 'VALIDATION_ERROR'
        self.details = details or {}
        self.context = context or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = f"[{self.code}] {self.message}"
        if self.details:
            error_str += f"\nDetails: {self.details}"
        if self.context:
            error_str += f"\nContext: {self.context}"
        return error_str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary format."""
        return {
            'code': self.code,
            'message': self.message,
            'details': self.details,
            'context': self.context
        }

class ConfigurationError(Exception):
    """Exception raised for configuration-related errors.
    
    Attributes:
        message -- explanation of the error
        config_key -- the configuration key that caused the error
        expected_type -- expected type of the configuration value
        received_type -- actual type of the configuration value
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        expected_type: Optional[str] = None,
        received_type: Optional[str] = None
    ):
        self.message = message
        self.config_key = config_key
        self.expected_type = expected_type
        self.received_type = received_type
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = f"Configuration Error: {self.message}"
        if self.config_key:
            error_str += f"\nKey: {self.config_key}"
        if self.expected_type and self.received_type:
            error_str += f"\nExpected type: {self.expected_type}, got: {self.received_type}"
        return error_str

class ResourceError(Exception):
    """Exception raised for resource-related errors.
    
    Attributes:
        message -- explanation of the error
        resource_type -- type of resource that caused the error
        resource_id -- identifier of the resource
        operation -- operation that failed
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        operation: Optional[str] = None
    ):
        self.message = message
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.operation = operation
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = f"Resource Error: {self.message}"
        if self.resource_type:
            error_str += f"\nResource Type: {self.resource_type}"
        if self.resource_id:
            error_str += f"\nResource ID: {self.resource_id}"
        if self.operation:
            error_str += f"\nOperation: {self.operation}"
        return error_str

class ServiceError(Exception):
    """Exception raised for service-related errors.
    
    Attributes:
        message -- explanation of the error
        service_name -- name of the service that raised the error
        operation -- operation that failed
        details -- additional error details
    """
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.service_name = service_name
        self.operation = operation
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = f"Service Error: {self.message}"
        if self.service_name:
            error_str += f"\nService: {self.service_name}"
        if self.operation:
            error_str += f"\nOperation: {self.operation}"
        if self.details:
            error_str += f"\nDetails: {self.details}"
        return error_str

class AuthenticationError(Exception):
    """Exception raised for authentication-related errors.
    
    Attributes:
        message -- explanation of the error
        user_id -- ID of the user (if available)
        auth_method -- authentication method that failed
    """
    
    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        auth_method: Optional[str] = None
    ):
        self.message = message
        self.user_id = user_id
        self.auth_method = auth_method
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = f"Authentication Error: {self.message}"
        if self.user_id:
            error_str += f"\nUser ID: {self.user_id}"
        if self.auth_method:
            error_str += f"\nAuth Method: {self.auth_method}"
        return error_str

class AuthorizationError(Exception):
    """Exception raised for authorization-related errors.
    
    Attributes:
        message -- explanation of the error
        user_id -- ID of the user
        required_permission -- permission that was required
        resource -- resource that was accessed
    """
    
    def __init__(
        self,
        message: str,
        user_id: Optional[str] = None,
        required_permission: Optional[str] = None,
        resource: Optional[str] = None
    ):
        self.message = message
        self.user_id = user_id
        self.required_permission = required_permission
        self.resource = resource
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        error_str = f"Authorization Error: {self.message}"
        if self.user_id:
            error_str += f"\nUser ID: {self.user_id}"
        if self.required_permission:
            error_str += f"\nRequired Permission: {self.required_permission}"
        if self.resource:
            error_str += f"\nResource: {self.resource}"
        return error_str 