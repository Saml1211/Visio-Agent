import pytest
from pathlib import Path
import tempfile
import json
import aiofiles
from datetime import datetime
from src.services.data_validation_service import (
    DataValidationService,
    DataType,
    DataSource,
    ValidationRule,
    ValidationResult,
    ValidationError
)

@pytest.fixture
def temp_rules_dir():
    """Create a temporary directory for validation rules"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
async def validation_service(temp_rules_dir):
    """Create a test validation service"""
    service = DataValidationService(rules_dir=temp_rules_dir)
    return service

@pytest.fixture
async def sample_rules(temp_rules_dir):
    """Create sample validation rules"""
    rules = [
        {
            "name": "username",
            "data_type": "string",
            "required": True,
            "min_length": 3,
            "max_length": 50,
            "regex_pattern": "^[a-zA-Z0-9_]+$",
            "error_message": "Username must be alphanumeric"
        },
        {
            "name": "age",
            "data_type": "integer",
            "required": True,
            "min_value": 0,
            "max_value": 150
        },
        {
            "name": "email",
            "data_type": "email",
            "required": True
        }
    ]
    
    # Create rules file
    rules_file = temp_rules_dir / "user_input_rules.json"
    async with aiofiles.open(rules_file, 'w') as f:
        await f.write(json.dumps(rules))
    
    return rules

@pytest.mark.asyncio
async def test_load_validation_rules(validation_service, sample_rules):
    """Test loading validation rules from file"""
    await validation_service.load_validation_rules()
    
    assert DataSource.USER_INPUT.value in validation_service.validation_rules
    rules = validation_service.validation_rules[DataSource.USER_INPUT.value]
    assert len(rules) == 3
    
    username_rule = next(r for r in rules if r.name == "username")
    assert username_rule.data_type == DataType.STRING
    assert username_rule.required
    assert username_rule.min_length == 3
    assert username_rule.max_length == 50
    assert username_rule.regex_pattern == "^[a-zA-Z0-9_]+$"

@pytest.mark.asyncio
async def test_save_validation_rules(validation_service):
    """Test saving validation rules to file"""
    # Add some rules
    rule = ValidationRule(
        name="test_field",
        data_type=DataType.STRING,
        required=True,
        min_length=5
    )
    validation_service.add_validation_rule(DataSource.API, rule)
    
    # Save rules
    await validation_service.save_validation_rules(DataSource.API)
    
    # Check file exists
    rules_file = validation_service.rules_dir / "api_rules.json"
    assert rules_file.exists()
    
    # Verify contents
    async with aiofiles.open(rules_file, 'r') as f:
        content = await f.read()
        rules = json.loads(content)
        assert len(rules) == 1
        assert rules[0]["name"] == "test_field"
        assert rules[0]["data_type"] == "string"
        assert rules[0]["required"] is True
        assert rules[0]["min_length"] == 5

@pytest.mark.asyncio
async def test_add_validation_rule(validation_service):
    """Test adding a new validation rule"""
    rule = ValidationRule(
        name="test_field",
        data_type=DataType.INTEGER,
        required=True,
        min_value=0,
        max_value=100
    )
    
    validation_service.add_validation_rule(DataSource.DOCUMENT, rule)
    
    assert DataSource.DOCUMENT.value in validation_service.validation_rules
    rules = validation_service.validation_rules[DataSource.DOCUMENT.value]
    assert len(rules) == 1
    assert rules[0].name == "test_field"
    
    # Test duplicate rule
    with pytest.raises(ValidationError):
        validation_service.add_validation_rule(DataSource.DOCUMENT, rule)

@pytest.mark.asyncio
async def test_remove_validation_rule(validation_service):
    """Test removing a validation rule"""
    rule = ValidationRule(
        name="test_field",
        data_type=DataType.STRING,
        required=True
    )
    
    validation_service.add_validation_rule(DataSource.VISIO, rule)
    assert len(validation_service.validation_rules[DataSource.VISIO.value]) == 1
    
    validation_service.remove_validation_rule(DataSource.VISIO, "test_field")
    assert len(validation_service.validation_rules[DataSource.VISIO.value]) == 0

@pytest.mark.asyncio
async def test_validate_data(validation_service, sample_rules):
    """Test data validation"""
    await validation_service.load_validation_rules()
    
    # Test valid data
    valid_data = {
        "username": "john_doe",
        "age": 25,
        "email": "john@example.com"
    }
    
    results = validation_service.validate_data(
        valid_data,
        DataSource.USER_INPUT
    )
    assert all(r.is_valid for r in results)
    
    # Test invalid data
    invalid_data = {
        "username": "j",  # Too short
        "age": 200,  # Too high
        "email": "invalid-email"  # Invalid format
    }
    
    results = validation_service.validate_data(
        invalid_data,
        DataSource.USER_INPUT
    )
    assert not any(r.is_valid for r in results)
    
    # Test missing required field
    incomplete_data = {
        "username": "john_doe",
        "age": 25
        # Missing email
    }
    
    results = validation_service.validate_data(
        incomplete_data,
        DataSource.USER_INPUT
    )
    assert any(not r.is_valid and "missing" in r.errors[0]["message"]
              for r in results)

@pytest.mark.asyncio
async def test_validate_types(validation_service):
    """Test type validation"""
    # String validation
    rule = ValidationRule(
        name="string_field",
        data_type=DataType.STRING
    )
    result = validation_service._validate_field("string_field", "test", rule)
    assert result.is_valid
    
    result = validation_service._validate_field("string_field", 123, rule)
    assert not result.is_valid
    
    # Integer validation
    rule = ValidationRule(
        name="int_field",
        data_type=DataType.INTEGER
    )
    result = validation_service._validate_field("int_field", 123, rule)
    assert result.is_valid
    
    result = validation_service._validate_field("int_field", "123", rule)
    assert not result.is_valid
    
    # Date validation
    rule = ValidationRule(
        name="date_field",
        data_type=DataType.DATE
    )
    result = validation_service._validate_field(
        "date_field",
        "2024-03-14T12:00:00",
        rule
    )
    assert result.is_valid
    
    result = validation_service._validate_field(
        "date_field",
        "invalid-date",
        rule
    )
    assert not result.is_valid

@pytest.mark.asyncio
async def test_custom_validator(validation_service):
    """Test custom validation function"""
    def validate_even(value):
        return isinstance(value, int) and value % 2 == 0
    
    rule = ValidationRule(
        name="even_number",
        data_type=DataType.INTEGER,
        custom_validator=validate_even,
        error_message="Number must be even"
    )
    
    result = validation_service._validate_field("even_number", 4, rule)
    assert result.is_valid
    
    result = validation_service._validate_field("even_number", 3, rule)
    assert not result.is_valid
    assert "Number must be even" in result.errors[0]["message"]

@pytest.mark.asyncio
async def test_regex_validation(validation_service):
    """Test regex pattern validation"""
    rule = ValidationRule(
        name="code",
        data_type=DataType.STRING,
        regex_pattern=r"^[A-Z]{2}\d{4}$",
        error_message="Code must be 2 uppercase letters followed by 4 digits"
    )
    
    result = validation_service._validate_field("code", "AB1234", rule)
    assert result.is_valid
    
    result = validation_service._validate_field("code", "AB123", rule)
    assert not result.is_valid
    assert "Code must be" in result.errors[0]["message"]

@pytest.mark.asyncio
async def test_value_range_validation(validation_service):
    """Test value range validation"""
    rule = ValidationRule(
        name="score",
        data_type=DataType.FLOAT,
        min_value=0.0,
        max_value=100.0
    )
    
    result = validation_service._validate_field("score", 75.5, rule)
    assert result.is_valid
    
    result = validation_service._validate_field("score", -1.0, rule)
    assert not result.is_valid
    assert "at least" in result.errors[0]["message"]
    
    result = validation_service._validate_field("score", 101.0, rule)
    assert not result.is_valid
    assert "at most" in result.errors[0]["message"] 