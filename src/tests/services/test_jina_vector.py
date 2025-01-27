import pytest
from src.services.vector_store.eve_adapter import EVEAdapter
from src.services.exceptions import ValidationError

@pytest.fixture
def mock_eve_adapter():
    return EVEAdapter()

async def test_vector_validation(mock_eve_adapter):
    """Test vector validation"""
    test_input = {"text": "test content"}
    result = await mock_eve_adapter.validate_input(test_input)
    assert result is True

async def test_vector_validation_error(mock_eve_adapter):
    """Test vector validation with invalid input"""
    with pytest.raises(ValidationError):
        await mock_eve_adapter.validate_input(None) 