import pytest
from typing import Dict, List, Tuple
from src.services.visio.config import ConnectorConfig, ShapeConfig
from src.services.connector_routing import ConnectorRouter
from src.services.exceptions import VisioRoutingError

MAX_ALLOWED_CROSSINGS = 3

@pytest.fixture
def router():
    return ConnectorRouter()

@pytest.fixture
def create_test_diagram():
    def _create_diagram():
        return {
            "shapes": [
                ShapeConfig(
                    id="shape1",
                    type="rectangle",
                    position={"x": 0, "y": 0},
                    size={"width": 1, "height": 1},
                    style={}
                ),
                ShapeConfig(
                    id="shape2",
                    type="rectangle",
                    position={"x": 5, "y": 5},
                    size={"width": 1, "height": 1},
                    style={}
                )
            ],
            "connections": [
                {
                    "source": "shape1",
                    "target": "shape2"
                }
            ]
        }
    return _create_diagram

async def test_connector_routing(router, create_test_diagram):
    """Test basic connector routing"""
    diagram = create_test_diagram()
    routing = await router.apply_routing(diagram)
    crossings = count_line_crossings(routing)
    assert crossings <= MAX_ALLOWED_CROSSINGS

def count_line_crossings(routing: Dict) -> int:
    """Count number of connector crossings"""
    crossings = 0
    connectors = routing.get("connectors", [])
    for i, conn1 in enumerate(connectors):
        for conn2 in connectors[i+1:]:
            if lines_intersect(conn1["points"], conn2["points"]):
                crossings += 1
    return crossings

def lines_intersect(points1: List[Dict[str, float]], 
                   points2: List[Dict[str, float]]) -> bool:
    """Check if two line segments intersect"""
    if not points1 or not points2:
        return False
        
    # Convert points to tuples for easier handling
    line1 = [(p["x"], p["y"]) for p in points1]
    line2 = [(p["x"], p["y"]) for p in points2]
    
    # Check each segment pair for intersection
    for i in range(len(line1) - 1):
        for j in range(len(line2) - 1):
            if segments_intersect(line1[i], line1[i+1], 
                                line2[j], line2[j+1]):
                return True
    return False

def segments_intersect(p1: Tuple[float, float], 
                      p2: Tuple[float, float],
                      p3: Tuple[float, float], 
                      p4: Tuple[float, float]) -> bool:
    """Check if two line segments intersect"""
    def ccw(A: Tuple[float, float], 
            B: Tuple[float, float], 
            C: Tuple[float, float]) -> bool:
        return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])
    
    return ccw(p1,p3,p4) != ccw(p2,p3,p4) and ccw(p1,p2,p3) != ccw(p1,p2,p4)

async def test_connector_style(router, create_test_diagram):
    """Test connector style application"""
    diagram = create_test_diagram()
    routing = await router.apply_routing(diagram)
    for connector in routing.get("connectors", []):
        assert "style" in connector
        assert "routing_style" in connector

class MockShape:
    """Mock shape for testing"""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = 1
        self.height = 1

def setup_generator() -> Dict:
    """Setup test generator with mock shapes"""
    return {
        "shapes": {
            "shape1": MockShape(0, 0),
            "shape2": MockShape(5, 5)
        }
    }

async def test_analyze_crossings(router):
    """Test crossing analysis"""
    generator = setup_generator()
    crossings = await router.analyze_crossings(generator["shapes"])
    assert isinstance(crossings, dict)
    assert "total_crossings" in crossings 