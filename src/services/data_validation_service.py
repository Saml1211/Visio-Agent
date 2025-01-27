from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
import re
import logging
from datetime import datetime
from pathlib import Path
import json
import aiofiles
from .exceptions import ValidationError

logger = logging.getLogger(__name__)

class DataType(str, Enum):
    """Supported data types for validation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    REGEX = "regex"

class DataSource(str, Enum):
    """Sources of data for validation"""
    DOCUMENT = "document"
    API = "api"
    USER_INPUT = "user_input"
    PROCESSED_OUTPUT = "processed_output"
    VISIO = "visio"

@dataclass
class ValidationRule:
    """Represents a single validation rule"""
    name: str
    data_type: DataType
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    allowed_values: Optional[List[Any]] = None
    regex_pattern: Optional[str] = None
    custom_validator: Optional[Callable[[Any], bool]] = None
    error_message: Optional[str] = None

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[Dict[str, Any]]
    field_name: str
    value: Any
    rule_name: str
    timestamp: datetime

class DataValidationService:
    """Service for managing and applying data validation rules"""
    
    def __init__(self, rules_dir: Optional[Path] = None):
        """Initialize the validation service
        
        Args:
            rules_dir: Directory containing validation rule configurations
        """
        self.rules_dir = rules_dir or Path("config/validation_rules")
        self.rules_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize rule storage
        self.validation_rules: Dict[str, Dict[str, List[ValidationRule]]] = {}
        self.load_validation_rules()
        
        logger.info(
            f"Initialized DataValidationService with "
            f"{sum(len(rules) for rules in self.validation_rules.values())} rules"
        )
    
    async def load_validation_rules(self) -> None:
        """Load validation rules from configuration files"""
        try:
            for source in DataSource:
                config_file = self.rules_dir / f"{source.value}_rules.json"
                if config_file.exists():
                    async with aiofiles.open(config_file, 'r') as f:
                        content = await f.read()
                        rules_config = json.loads(content)
                        
                        self.validation_rules[source.value] = []
                        for rule_config in rules_config:
                            rule = ValidationRule(
                                name=rule_config["name"],
                                data_type=DataType(rule_config["data_type"]),
                                required=rule_config.get("required", False),
                                min_length=rule_config.get("min_length"),
                                max_length=rule_config.get("max_length"),
                                min_value=rule_config.get("min_value"),
                                max_value=rule_config.get("max_value"),
                                allowed_values=rule_config.get("allowed_values"),
                                regex_pattern=rule_config.get("regex_pattern"),
                                error_message=rule_config.get("error_message")
                            )
                            self.validation_rules[source.value].append(rule)
        
        except Exception as e:
            logger.error(f"Error loading validation rules: {str(e)}")
            raise ValidationError(f"Failed to load validation rules: {str(e)}")
    
    async def save_validation_rules(self, source: DataSource) -> None:
        """Save validation rules to configuration file
        
        Args:
            source: Data source to save rules for
        """
        try:
            rules = self.validation_rules.get(source.value, [])
            rules_config = []
            
            for rule in rules:
                rule_dict = {
                    "name": rule.name,
                    "data_type": rule.data_type.value,
                    "required": rule.required
                }
                
                # Add optional fields if set
                if rule.min_length is not None:
                    rule_dict["min_length"] = rule.min_length
                if rule.max_length is not None:
                    rule_dict["max_length"] = rule.max_length
                if rule.min_value is not None:
                    rule_dict["min_value"] = rule.min_value
                if rule.max_value is not None:
                    rule_dict["max_value"] = rule.max_value
                if rule.allowed_values is not None:
                    rule_dict["allowed_values"] = rule.allowed_values
                if rule.regex_pattern is not None:
                    rule_dict["regex_pattern"] = rule.regex_pattern
                if rule.error_message is not None:
                    rule_dict["error_message"] = rule.error_message
                
                rules_config.append(rule_dict)
            
            config_file = self.rules_dir / f"{source.value}_rules.json"
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(rules_config, indent=2))
            
            logger.info(f"Saved {len(rules)} validation rules for {source.value}")
            
        except Exception as e:
            logger.error(f"Error saving validation rules: {str(e)}")
            raise ValidationError(f"Failed to save validation rules: {str(e)}")
    
    def add_validation_rule(
        self,
        source: DataSource,
        rule: ValidationRule
    ) -> None:
        """Add a new validation rule
        
        Args:
            source: Data source to add rule for
            rule: Validation rule to add
        """
        if source.value not in self.validation_rules:
            self.validation_rules[source.value] = []
        
        # Check for duplicate rule names
        if any(r.name == rule.name for r in self.validation_rules[source.value]):
            raise ValidationError(f"Rule with name '{rule.name}' already exists")
        
        self.validation_rules[source.value].append(rule)
        logger.info(f"Added validation rule '{rule.name}' for {source.value}")
    
    def remove_validation_rule(
        self,
        source: DataSource,
        rule_name: str
    ) -> None:
        """Remove a validation rule
        
        Args:
            source: Data source to remove rule from
            rule_name: Name of rule to remove
        """
        if source.value in self.validation_rules:
            self.validation_rules[source.value] = [
                rule for rule in self.validation_rules[source.value]
                if rule.name != rule_name
            ]
            logger.info(f"Removed validation rule '{rule_name}' from {source.value}")
    
    def validate_data(
        self,
        data: Dict[str, Any],
        source: DataSource
    ) -> List[ValidationResult]:
        """Validate data against rules for a specific source
        
        Args:
            data: Data to validate
            source: Source of the data
            
        Returns:
            List of validation results
        """
        results = []
        rules = self.validation_rules.get(source.value, [])
        
        for field_name, value in data.items():
            field_rules = [r for r in rules if r.name == field_name]
            
            if not field_rules:
                continue
            
            for rule in field_rules:
                result = self._validate_field(field_name, value, rule)
                results.append(result)
        
        # Check for missing required fields
        for rule in rules:
            if rule.required and rule.name not in data:
                results.append(ValidationResult(
                    is_valid=False,
                    errors=[{
                        "type": "missing_required_field",
                        "message": f"Required field '{rule.name}' is missing"
                    }],
                    field_name=rule.name,
                    value=None,
                    rule_name=rule.name,
                    timestamp=datetime.now()
                ))
        
        return results
    
    def _validate_field(
        self,
        field_name: str,
        value: Any,
        rule: ValidationRule
    ) -> ValidationResult:
        """Validate a single field against a rule
        
        Args:
            field_name: Name of the field
            value: Value to validate
            rule: Validation rule to apply
            
        Returns:
            Validation result
        """
        errors = []
        
        # Type validation
        if not self._validate_type(value, rule.data_type):
            errors.append({
                "type": "invalid_type",
                "message": f"Expected type {rule.data_type.value}"
            })
            return ValidationResult(
                is_valid=False,
                errors=errors,
                field_name=field_name,
                value=value,
                rule_name=rule.name,
                timestamp=datetime.now()
            )
        
        # Length validation
        if rule.min_length is not None and len(str(value)) < rule.min_length:
            errors.append({
                "type": "min_length",
                "message": f"Length must be at least {rule.min_length}"
            })
        
        if rule.max_length is not None and len(str(value)) > rule.max_length:
            errors.append({
                "type": "max_length",
                "message": f"Length must be at most {rule.max_length}"
            })
        
        # Value range validation
        if rule.min_value is not None and value < rule.min_value:
            errors.append({
                "type": "min_value",
                "message": f"Value must be at least {rule.min_value}"
            })
        
        if rule.max_value is not None and value > rule.max_value:
            errors.append({
                "type": "max_value",
                "message": f"Value must be at most {rule.max_value}"
            })
        
        # Allowed values validation
        if rule.allowed_values is not None and value not in rule.allowed_values:
            errors.append({
                "type": "invalid_value",
                "message": f"Value must be one of {rule.allowed_values}"
            })
        
        # Regex pattern validation
        if rule.regex_pattern is not None:
            if not re.match(rule.regex_pattern, str(value)):
                errors.append({
                    "type": "pattern_mismatch",
                    "message": rule.error_message or "Value does not match pattern"
                })
        
        # Custom validator
        if rule.custom_validator is not None:
            try:
                if not rule.custom_validator(value):
                    errors.append({
                        "type": "custom_validation",
                        "message": rule.error_message or "Custom validation failed"
                    })
            except Exception as e:
                errors.append({
                    "type": "custom_validation_error",
                    "message": f"Custom validator error: {str(e)}"
                })
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            field_name=field_name,
            value=value,
            rule_name=rule.name,
            timestamp=datetime.now()
        )
    
    def _validate_type(self, value: Any, expected_type: DataType) -> bool:
        """Validate value against expected type
        
        Args:
            value: Value to validate
            expected_type: Expected data type
            
        Returns:
            True if type is valid, False otherwise
        """
        try:
            if expected_type == DataType.STRING:
                return isinstance(value, str)
            elif expected_type == DataType.INTEGER:
                return isinstance(value, int)
            elif expected_type == DataType.FLOAT:
                return isinstance(value, (int, float))
            elif expected_type == DataType.BOOLEAN:
                return isinstance(value, bool)
            elif expected_type == DataType.LIST:
                return isinstance(value, list)
            elif expected_type == DataType.DICT:
                return isinstance(value, dict)
            elif expected_type == DataType.DATE:
                return isinstance(value, (datetime, str)) and self._is_valid_date(value)
            elif expected_type == DataType.EMAIL:
                return isinstance(value, str) and self._is_valid_email(value)
            elif expected_type == DataType.URL:
                return isinstance(value, str) and self._is_valid_url(value)
            elif expected_type == DataType.REGEX:
                return isinstance(value, str)
            return False
        except Exception:
            return False
    
    def _is_valid_date(self, value: Union[datetime, str]) -> bool:
        """Check if value is a valid date
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid date, False otherwise
        """
        if isinstance(value, datetime):
            return True
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False
    
    def _is_valid_email(self, value: str) -> bool:
        """Check if value is a valid email
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid email, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, value))
    
    def _is_valid_url(self, value: str) -> bool:
        """Check if value is a valid URL
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid URL, False otherwise
        """
        pattern = r'^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$'
        return bool(re.match(pattern, value))

# Limitations:
# 1. No support for nested object validation
# 2. Limited custom validation capabilities
# 3. No support for conditional validation rules
# 4. Basic type checking without complex type validation
# 5. No support for cross-field validation
# 6. Simple file-based storage may not scale well
# 7. No versioning support for validation rules
# 8. Limited error message customization 