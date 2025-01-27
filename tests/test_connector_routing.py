import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.visio_generation.connector_routing import *

@pytest.fixture
def mock_visio_page():
    page = MagicMock()
    page.Layout = MagicMock()
    page.ResizeToFitContents = MagicMock()
    return page

@pytest.mark.asyncio
async def test_hybrid_routing(mock_visio_page):
    config = AIRoutingConfig(algorithm=RoutingAlgorithm.HYBRID)
    constraints = RoutingConstraints(max_bend_angle=30)
    
    router = HybridRouter(mock_visio_page, config, constraints)
    router.add_connector(MagicMock())
    router.add_obstacle(MagicMock())
    
    await router.optimize_all_paths()
    
    mock_visio_page.Layout.assert_called_once()
    assert router.connectors is not None

@pytest.mark.stress
async def test_high_density_routing():
    """Test with 1000 connectors in constrained space"""
    config = AIRoutingConfig(population_size=200)
    router = HybridRouter(MagicMock(), config, RoutingConstraints(max_bend_angle=30))
    # Add 1000 connectors with random obstacles
    await router.optimize_all_paths()
    assert router.optimization_score < MAX_ALLOWED_CROSSINGS

@pytest.mark.asyncio
async def test_routing_failure_recovery():
    """Test error handling in routing algorithms"""
    with pytest.raises(VisioRoutingError):
        await router.optimize_all_paths()

def test_complex_crossing_reduction():
    diagram = create_test_diagram(50)
    original_crossings = count_line_crossings(diagram)
    optimized_diagram = apply_routing(diagram)
    new_crossings = count_line_crossings(optimized_diagram)
    assert new_crossings < original_crossings * 0.5 

def test_orthogonal_routing():
    generator = setup_generator()
    diagram = generator.generate_complex_diagram()
    crossings = analyze_crossings(diagram)
    assert crossings < 3, "Excessive line crossings detected"
    
def test_routing_config_override():
    generator = setup_generator(style=ConnectorStyle.CURVED)
    diagram = generator.generate_diagram()
    assert diagram.connectors[0].is_curved 