"""
Tests for custom exceptions in the LLD Automation Project.
"""

import pytest
from src.exceptions import (
    ValidationError,
    ConfigurationError,
    ResourceError,
    ServiceError,
    AuthenticationError,
    AuthorizationError
)

def test_validation_error():
    """Test ValidationError creation and string representation"""
    # Test basic error
    error = ValidationError("Invalid input")
    assert str(error) == "[VALIDATION_ERROR] Invalid input"
    assert error.code == "VALIDATION_ERROR"
    assert error.details == {}
    assert error.context == {}
    
    # Test with all attributes
    error = ValidationError(
        message="Color contrast too low",
        code="COLOR_001",
        details={"contrast_ratio": 2.5},
        context={"element_id": "text_1"}
    )
    error_str = str(error)
    assert "[COLOR_001]" in error_str
    assert "Color contrast too low" in error_str
    assert "contrast_ratio" in error_str
    assert "element_id" in error_str
    
    # Test to_dict method
    error_dict = error.to_dict()
    assert error_dict["code"] == "COLOR_001"
    assert error_dict["message"] == "Color contrast too low"
    assert error_dict["details"]["contrast_ratio"] == 2.5
    assert error_dict["context"]["element_id"] == "text_1"

def test_configuration_error():
    """Test ConfigurationError creation and string representation"""
    # Test basic error
    error = ConfigurationError("Missing configuration")
    assert "Configuration Error: Missing configuration" in str(error)
    
    # Test with all attributes
    error = ConfigurationError(
        message="Invalid value type",
        config_key="min_contrast",
        expected_type="float",
        received_type="str"
    )
    error_str = str(error)
    assert "Invalid value type" in error_str
    assert "min_contrast" in error_str
    assert "float" in error_str
    assert "str" in error_str

def test_resource_error():
    """Test ResourceError creation and string representation"""
    # Test basic error
    error = ResourceError("Resource not found")
    assert "Resource Error: Resource not found" in str(error)
    
    # Test with all attributes
    error = ResourceError(
        message="Failed to load stencil",
        resource_type="Visio.Stencil",
        resource_id="network_shapes.vssx",
        operation="load"
    )
    error_str = str(error)
    assert "Failed to load stencil" in error_str
    assert "Visio.Stencil" in error_str
    assert "network_shapes.vssx" in error_str
    assert "load" in error_str

def test_service_error():
    """Test ServiceError creation and string representation"""
    # Test basic error
    error = ServiceError("Service unavailable")
    assert "Service Error: Service unavailable" in str(error)
    
    # Test with all attributes
    error = ServiceError(
        message="API request failed",
        service_name="VisioGenerationService",
        operation="generate_diagram",
        details={"status_code": 500}
    )
    error_str = str(error)
    assert "API request failed" in error_str
    assert "VisioGenerationService" in error_str
    assert "generate_diagram" in error_str
    assert "status_code" in error_str

def test_authentication_error():
    """Test AuthenticationError creation and string representation"""
    # Test basic error
    error = AuthenticationError("Authentication failed")
    assert "Authentication Error: Authentication failed" in str(error)
    
    # Test with all attributes
    error = AuthenticationError(
        message="Invalid credentials",
        user_id="user123",
        auth_method="JWT"
    )
    error_str = str(error)
    assert "Invalid credentials" in error_str
    assert "user123" in error_str
    assert "JWT" in error_str

def test_authorization_error():
    """Test AuthorizationError creation and string representation"""
    # Test basic error
    error = AuthorizationError("Unauthorized access")
    assert "Authorization Error: Unauthorized access" in str(error)
    
    # Test with all attributes
    error = AuthorizationError(
        message="Insufficient permissions",
        user_id="user123",
        required_permission="ADMIN",
        resource="diagram_1"
    )
    error_str = str(error)
    assert "Insufficient permissions" in error_str
    assert "user123" in error_str
    assert "ADMIN" in error_str
    assert "diagram_1" in error_str

def test_exception_inheritance():
    """Test that all custom exceptions inherit from Exception"""
    exceptions = [
        ValidationError("test"),
        ConfigurationError("test"),
        ResourceError("test"),
        ServiceError("test"),
        AuthenticationError("test"),
        AuthorizationError("test")
    ]
    
    for error in exceptions:
        assert isinstance(error, Exception)
        # Test that the message is preserved
        assert "test" in str(error)

def test_validation_error_with_empty_optionals():
    """Test ValidationError with None values for optional parameters"""
    error = ValidationError(
        message="Test error",
        code=None,
        details=None,
        context=None
    )
    assert error.code == "VALIDATION_ERROR"  # Default value
    assert error.details == {}  # Empty dict
    assert error.context == {}  # Empty dict
    
    error_dict = error.to_dict()
    assert all(key in error_dict for key in ["code", "message", "details", "context"])

def test_error_message_formatting():
    """Test error message formatting across all exception types"""
    test_cases = [
        (
            ValidationError,
            {"message": "test", "code": "TEST_001"},
            lambda e: "[TEST_001]" in str(e)
        ),
        (
            ConfigurationError,
            {"message": "test", "config_key": "key"},
            lambda e: "key" in str(e)
        ),
        (
            ResourceError,
            {"message": "test", "resource_type": "type"},
            lambda e: "type" in str(e)
        ),
        (
            ServiceError,
            {"message": "test", "service_name": "service"},
            lambda e: "service" in str(e)
        ),
        (
            AuthenticationError,
            {"message": "test", "auth_method": "method"},
            lambda e: "method" in str(e)
        ),
        (
            AuthorizationError,
            {"message": "test", "required_permission": "permission"},
            lambda e: "permission" in str(e)
        )
    ]
    
    for exception_class, kwargs, validation_func in test_cases:
        error = exception_class(**kwargs)
        assert validation_func(error)
        assert isinstance(str(error), str)
        assert kwargs["message"] in str(error) 