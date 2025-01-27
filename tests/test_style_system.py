import pytest
from unittest.mock import Mock
from src.services.style_resolver import StyleResolver
from src.services.style_validator import StyleValidator

@pytest.fixture
def mock_guide():
    guide = Mock()
    guide.get_rule.side_effect = lambda t: {
        'shape': {'fill': '#FFFFFF', 'outline': '1pt solid'},
        'connector': {'arrow': 'standard', 'color': '#0000FF'},
        'font': {'size': '12pt', 'family': 'Arial'}
    }.get(t, {})
    return guide

def test_schematic_inheritance(mock_guide):
    resolver = StyleResolver(mock_guide)
    styles = resolver.resolve_styles('schematic')
    
    assert styles['fill'] == '#FFFFFF'  # From shape
    assert styles['arrow'] == 'standard'  # From connector override
    assert styles['size'] == '12pt'  # From font

def test_validation_happy_path():
    validator = StyleValidator()
    assert validator.validate_rule(
        {'TextStyle': 'Arial', 'TextSize': '12pt'}, 
        'font'
    )

def test_validation_failure():
    validator = StyleValidator()
    assert not validator.validate_rule(
        {'InvalidProp': 12, 'BadColor': '00XXFF'},
        'font'
    ) 