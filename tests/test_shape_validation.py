import pytest
from src.services.visio_generation.shape_validation import (
    ShapePropertyValidator,
    ValidationError,
    ColorFormat
)

def test_validate_rgb_color():
    """Test validation of RGB color format"""
    # Valid RGB colors
    assert ShapePropertyValidator.validate_color("255,0,0", "fill_color") is None
    assert ShapePropertyValidator.validate_color("0,255,0", "fill_color") is None
    assert ShapePropertyValidator.validate_color("0,0,255", "fill_color") is None
    
    # Invalid RGB values
    error = ShapePropertyValidator.validate_color("256,0,0", "fill_color")
    assert error is not None
    assert error.error_type == "invalid_rgb_range"
    
    error = ShapePropertyValidator.validate_color("-1,0,0", "fill_color")
    assert error is not None
    assert error.error_type == "invalid_rgb_range"
    
    # Invalid format
    error = ShapePropertyValidator.validate_color("255,0", "fill_color")
    assert error is not None
    assert error.error_type == "invalid_color_format"

def test_validate_hex_color():
    """Test validation of HEX color format"""
    # Valid HEX colors
    assert ShapePropertyValidator.validate_color("#FF0000", "fill_color") is None
    assert ShapePropertyValidator.validate_color("00FF00", "fill_color") is None
    assert ShapePropertyValidator.validate_color("#0000FF", "fill_color") is None
    
    # Invalid HEX values
    error = ShapePropertyValidator.validate_color("#GG0000", "fill_color")
    assert error is not None
    assert error.error_type == "color_validation_error"
    
    error = ShapePropertyValidator.validate_color("#12345", "fill_color")
    assert error is not None
    assert error.error_type == "invalid_color_format"

def test_validate_html_color():
    """Test validation of HTML color names"""
    # Valid HTML colors
    assert ShapePropertyValidator.validate_color("red", "fill_color") is None
    assert ShapePropertyValidator.validate_color("blue", "fill_color") is None
    assert ShapePropertyValidator.validate_color("GREEN", "fill_color") is None
    
    # Invalid HTML color
    error = ShapePropertyValidator.validate_color("not_a_color", "fill_color")
    assert error is not None
    assert error.error_type == "invalid_color_format"

def test_validate_numeric_values():
    """Test validation of numeric values"""
    # Valid numeric values
    assert ShapePropertyValidator.validate_numeric(10, "line_weight") is None
    assert ShapePropertyValidator.validate_numeric(0.5, "opacity", min_value=0, max_value=1) is None
    
    # Invalid numeric values
    error = ShapePropertyValidator.validate_numeric(-1, "line_weight", min_value=0)
    assert error is not None
    assert error.error_type == "below_minimum"
    
    error = ShapePropertyValidator.validate_numeric(2, "opacity", min_value=0, max_value=1)
    assert error is not None
    assert error.error_type == "above_maximum"
    
    error = ShapePropertyValidator.validate_numeric("not_a_number", "line_weight")
    assert error is not None
    assert error.error_type == "invalid_numeric"

def test_validate_font():
    """Test validation of font names"""
    available_fonts = ["Arial", "Times New Roman", "Calibri"]
    
    # Valid fonts
    assert ShapePropertyValidator.validate_font("Arial", "font_name", available_fonts) is None
    
    # Invalid fonts
    error = ShapePropertyValidator.validate_font("", "font_name")
    assert error is not None
    assert error.error_type == "empty_font_name"
    
    error = ShapePropertyValidator.validate_font(
        "NonexistentFont",
        "font_name",
        available_fonts
    )
    assert error is not None
    assert error.error_type == "unavailable_font"

def test_validate_text_style():
    """Test validation of text styles"""
    # Valid styles
    assert ShapePropertyValidator.validate_text_style("Bold", "text_style") is None
    assert ShapePropertyValidator.validate_text_style("Bold,Italic", "text_style") is None
    
    # Invalid styles
    error = ShapePropertyValidator.validate_text_style("NotAStyle", "text_style")
    assert error is not None
    assert error.error_type == "invalid_text_style"
    
    error = ShapePropertyValidator.validate_text_style("Bold,Invalid", "text_style")
    assert error is not None
    assert error.error_type == "invalid_text_style"

def test_validate_complete_shape_style():
    """Test validation of complete shape style"""
    style = {
        "fill_color": "255,0,0",
        "line_color": "#00FF00",
        "text_color": "blue",
        "line_weight": 2.0,
        "text_size": 12.0,
        "opacity": 0.8,
        "font_name": "Arial",
        "text_style": "Bold,Italic"
    }
    
    # Valid style
    errors = ShapePropertyValidator.validate_shape_style(
        style,
        available_fonts=["Arial"]
    )
    assert len(errors) == 0
    
    # Style with multiple errors
    invalid_style = {
        "fill_color": "256,0,0",  # Invalid RGB
        "line_weight": -1,        # Invalid weight
        "text_size": 1000,        # Too large
        "opacity": 2.0,           # Invalid opacity
        "font_name": "",          # Empty font
        "text_style": "Invalid"   # Invalid style
    }
    
    errors = ShapePropertyValidator.validate_shape_style(invalid_style)
    assert len(errors) == 6
    error_types = {e.error_type for e in errors}
    assert "invalid_rgb_range" in error_types
    assert "below_minimum" in error_types
    assert "above_maximum" in error_types
    assert "empty_font_name" in error_types
    assert "invalid_text_style" in error_types

def test_color_format_conversion():
    """Test color format conversion"""
    # RGB to RGB (no change)
    assert ShapePropertyValidator.convert_color_to_rgb("255,0,0") == "255,0,0"
    
    # HEX to RGB
    assert ShapePropertyValidator.convert_color_to_rgb("#FF0000") == "255,0,0"
    assert ShapePropertyValidator.convert_color_to_rgb("00FF00") == "0,255,0"
    
    # HTML name to RGB
    assert ShapePropertyValidator.convert_color_to_rgb("red") == "255,0,0"
    assert ShapePropertyValidator.convert_color_to_rgb("BLUE") == "0,0,255"
    
    # Invalid color
    with pytest.raises(ValueError):
        ShapePropertyValidator.convert_color_to_rgb("not_a_color") 