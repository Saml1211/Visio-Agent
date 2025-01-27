import pytest
from typing import Dict, Any

@pytest.fixture
def mock_validation_error():
    class ValidationError(Exception):
        pass
    return ValidationError

@pytest.fixture
def mock_visio_routing_error():
    class VisioRoutingError(Exception):
        pass
    return VisioRoutingError

@pytest.fixture
def mock_router():
    class MockRouter:
        async def apply_routing(self, diagram: Dict[str, Any]) -> Dict[str, Any]:
            return {"connectors": [], "total_crossings": 0}
            
        async def analyze_crossings(self, shapes: Dict[str, Any]) -> Dict[str, Any]:
            return {"total_crossings": 0}
    return MockRouter()

MAX_ALLOWED_CROSSINGS = 3 