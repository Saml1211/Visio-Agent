"""
Tests for the DeepValidator class.
"""

import pytest
import asyncio
from typing import Dict, Any
from src.services.deep_validator import DeepValidator
from src.models.validation_models import (
    ValidationResult,
    ValidationSeverity,
    ColorValidationResult,
    TextValidationResult,
    SpacingValidationResult
)
from src.exceptions import ValidationError

@pytest.fixture
def validator():
    """Create a validator instance for testing"""
    return DeepValidator()

@pytest.fixture
def sample_colors():
    """Sample color pairs for testing"""
    return [
        {
            'foreground': '#000000',  # Black
            'background': '#FFFFFF'   # White
        },
        {
            'foreground': '#FF0000',  # Red
            'background': '#FFFFFF'   # White
        }
    ]

@pytest.fixture
def sample_text_elements():
    """Sample text elements for testing"""
    return [
        {
            'content': 'Sample text for testing.',
            'font_size': 12,
            'font_family': 'Arial'
        },
        {
            'content': 'This is a longer piece of text that might be too long for comfortable reading in a diagram.',
            'font_size': 8,
            'font_family': 'Times New Roman'
        }
    ]

@pytest.fixture
def sample_elements():
    """Sample diagram elements for testing"""
    return [
        {
            'id': 'elem1',
            'x': 0,
            'y': 0,
            'width': 100,
            'height': 50
        },
        {
            'id': 'elem2',
            'x': 150,
            'y': 0,
            'width': 100,
            'height': 50
        }
    ]

@pytest.fixture
def sample_diagram_data(sample_colors, sample_text_elements, sample_elements):
    """Sample complete diagram data for testing"""
    return {
        'colors': sample_colors,
        'text_elements': sample_text_elements,
        'elements': sample_elements
    }

@pytest.mark.asyncio
async def test_validate_colors_success(validator, sample_colors):
    """Test successful color validation"""
    result = await validator.validate_colors(sample_colors)
    assert isinstance(result, ColorValidationResult)
    assert result.wcag_aa_pass
    assert result.contrast_ratio >= 4.5
    assert len(result.issues) == 0

@pytest.mark.asyncio
async def test_validate_colors_failure():
    """Test color validation with poor contrast"""
    validator = DeepValidator()
    colors = [{
        'foreground': '#777777',  # Gray
        'background': '#888888'   # Similar gray
    }]
    
    result = await validator.validate_colors(colors)
    assert not result.wcag_aa_pass
    assert len(result.issues) > 0
    assert result.issues[0].severity == ValidationSeverity.ERROR

@pytest.mark.asyncio
async def test_validate_text_success(validator, sample_text_elements):
    """Test successful text validation"""
    result = await validator.validate_text(sample_text_elements)
    assert isinstance(result, TextValidationResult)
    assert result.font_valid
    assert result.readability_score > 0
    assert len(result.issues) == 1  # One warning for small font size

@pytest.mark.asyncio
async def test_validate_text_failure():
    """Test text validation with readability issues"""
    validator = DeepValidator()
    text_elements = [{
        'content': 'x' * 300,  # Very long text
        'font_size': 6,       # Too small
        'font_family': 'Arial'
    }]
    
    result = await validator.validate_text(text_elements)
    assert len(result.issues) == 2  # Size and length issues
    assert not result.font_valid

@pytest.mark.asyncio
async def test_validate_spacing_success(validator, sample_elements):
    """Test successful spacing validation"""
    result = await validator.validate_spacing(sample_elements)
    assert isinstance(result, SpacingValidationResult)
    assert result.spacing_score > 0
    assert len(result.crowded_areas) == 0
    assert len(result.issues) == 0

@pytest.mark.asyncio
async def test_validate_spacing_failure():
    """Test spacing validation with crowding issues"""
    validator = DeepValidator()
    elements = [
        {
            'id': 'elem1',
            'x': 0,
            'y': 0,
            'width': 100,
            'height': 50
        },
        {
            'id': 'elem2',
            'x': 10,  # Too close to elem1
            'y': 0,
            'width': 100,
            'height': 50
        }
    ]
    
    result = await validator.validate_spacing(elements)
    assert len(result.crowded_areas) > 0
    assert len(result.issues) > 0
    assert result.issues[0].severity == ValidationSeverity.WARNING

@pytest.mark.asyncio
async def test_validate_diagram_success(validator, sample_diagram_data):
    """Test successful full diagram validation"""
    result = await validator.validate_diagram(sample_diagram_data)
    assert isinstance(result, ValidationResult)
    assert result.passed
    assert result.score > 0
    assert isinstance(result.color_results, ColorValidationResult)
    assert isinstance(result.text_results, TextValidationResult)
    assert isinstance(result.spacing_results, SpacingValidationResult)
    assert 'validation_time' in result.metadata

@pytest.mark.asyncio
async def test_validate_diagram_failure():
    """Test diagram validation with multiple issues"""
    validator = DeepValidator()
    bad_diagram_data = {
        'colors': [{
            'foreground': '#777777',
            'background': '#888888'
        }],
        'text_elements': [{
            'content': 'x' * 300,
            'font_size': 6
        }],
        'elements': [
            {'id': 'e1', 'x': 0, 'y': 0, 'width': 100, 'height': 50},
            {'id': 'e2', 'x': 10, 'y': 0, 'width': 100, 'height': 50}
        ]
    }
    
    result = await validator.validate_diagram(bad_diagram_data)
    assert not result.passed
    assert result.score < 50
    assert len(result.issues) > 0

@pytest.mark.asyncio
async def test_validation_error_handling():
    """Test error handling in validation"""
    validator = DeepValidator()
    
    with pytest.raises(ValidationError):
        await validator.validate_colors([{'invalid': 'color'}])
    
    with pytest.raises(ValidationError):
        await validator.validate_text([{'invalid': 'text'}])
    
    with pytest.raises(ValidationError):
        await validator.validate_spacing([{'invalid': 'element'}])

def test_color_parsing():
    """Test color parsing utility"""
    validator = DeepValidator()
    
    assert validator._parse_color('#000000') == (0, 0, 0)
    assert validator._parse_color('#FFFFFF') == (255, 255, 255)
    assert validator._parse_color('invalid') is None

def test_contrast_calculation():
    """Test contrast ratio calculation"""
    validator = DeepValidator()
    
    black = (0, 0, 0)
    white = (255, 255, 255)
    gray = (128, 128, 128)
    
    assert validator._calculate_contrast(black, white) > 20  # High contrast
    assert validator._calculate_contrast(gray, gray) == 0   # No contrast

def test_readability_calculation():
    """Test text readability scoring"""
    validator = DeepValidator()
    
    simple_text = "This is a simple sentence."
    complex_text = "This is a much longer and more complex sentence with multiple clauses and technical terminology."
    
    simple_score = validator._calculate_readability(simple_text)
    complex_score = validator._calculate_readability(complex_text)
    
    assert simple_score > complex_score
    assert 0 <= simple_score <= 100
    assert 0 <= complex_score <= 100

def test_distance_calculation():
    """Test element distance calculation"""
    validator = DeepValidator()
    
    elem1 = {'x': 0, 'y': 0}
    elem2 = {'x': 3, 'y': 4}
    
    distance = validator._calculate_distance(elem1, elem2)
    assert distance == 5  # 3-4-5 triangle

def test_area_calculations():
    """Test area calculation utilities"""
    validator = DeepValidator()
    
    elements = [
        {'x': 0, 'y': 0, 'width': 10, 'height': 10},
        {'x': 20, 'y': 20, 'width': 10, 'height': 10}
    ]
    
    total_area = validator._calculate_total_area(elements)
    used_area = validator._calculate_used_area(elements)
    
    assert total_area > 0
    assert used_area == 200  # 2 elements of 10x10 