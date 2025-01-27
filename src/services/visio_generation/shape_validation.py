import re
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ColorFormat(str, Enum):
    """Supported color formats"""
    RGB = "rgb"
    HEX = "hex"
    HTML = "html"

@dataclass
class ValidationError:
    """Represents a validation error"""
    property_name: str
    expected_value: Any
    actual_value: Any
    error_type: str
    details: Optional[str] = None

class ShapePropertyValidator:
    """Validates shape properties and styles"""
    
    # Regular expressions for color formats
    RGB_PATTERN = re.compile(r'^\d{1,3},\d{1,3},\d{1,3}$')
    HEX_PATTERN = re.compile(r'^#?[0-9a-fA-F]{6}$')
    HTML_COLOR_NAMES = {
        'red', 'green', 'blue', 'black', 'white', 'yellow', 'purple',
        'orange', 'gray', 'brown', 'pink', 'cyan', 'magenta'
    }
    
    @classmethod
    def validate_color(
        cls,
        color: str,
        property_name: str
    ) -> Optional[ValidationError]:
        """Validate a color value in any supported format"""
        try:
            # Try RGB format
            if cls.RGB_PATTERN.match(color):
                r, g, b = map(int, color.split(','))
                if not all(0 <= x <= 255 for x in (r, g, b)):
                    return ValidationError(
                        property_name=property_name,
                        expected_value="RGB values between 0-255",
                        actual_value=color,
                        error_type="invalid_rgb_range"
                    )
                return None
            
            # Try HEX format
            if cls.HEX_PATTERN.match(color):
                color = color.lstrip('#')
                # Convert to RGB for validation
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
                return None
            
            # Try HTML color name
            if color.lower() in cls.HTML_COLOR_NAMES:
                return None
            
            return ValidationError(
                property_name=property_name,
                expected_value="Valid color format (RGB, HEX, or HTML name)",
                actual_value=color,
                error_type="invalid_color_format"
            )
            
        except Exception as e:
            return ValidationError(
                property_name=property_name,
                expected_value="Valid color value",
                actual_value=color,
                error_type="color_validation_error",
                details=str(e)
            )
    
    @classmethod
    def validate_numeric(
        cls,
        value: Union[int, float],
        property_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Optional[ValidationError]:
        """Validate a numeric value within specified range"""
        try:
            num_value = float(value)
            
            if min_value is not None and num_value < min_value:
                return ValidationError(
                    property_name=property_name,
                    expected_value=f">= {min_value}",
                    actual_value=value,
                    error_type="below_minimum"
                )
            
            if max_value is not None and num_value > max_value:
                return ValidationError(
                    property_name=property_name,
                    expected_value=f"<= {max_value}",
                    actual_value=value,
                    error_type="above_maximum"
                )
            
            return None
            
        except (TypeError, ValueError) as e:
            return ValidationError(
                property_name=property_name,
                expected_value="Numeric value",
                actual_value=value,
                error_type="invalid_numeric",
                details=str(e)
            )
    
    @classmethod
    def validate_font(
        cls,
        font_name: str,
        property_name: str,
        available_fonts: Optional[List[str]] = None
    ) -> Optional[ValidationError]:
        """Validate a font name"""
        if not font_name:
            return ValidationError(
                property_name=property_name,
                expected_value="Non-empty font name",
                actual_value=font_name,
                error_type="empty_font_name"
            )
        
        if available_fonts and font_name not in available_fonts:
            return ValidationError(
                property_name=property_name,
                expected_value=f"One of {available_fonts}",
                actual_value=font_name,
                error_type="unavailable_font"
            )
        
        return None
    
    @classmethod
    def validate_text_style(
        cls,
        style: str,
        property_name: str
    ) -> Optional[ValidationError]:
        """Validate text style specification"""
        valid_styles = {'Bold', 'Italic', 'Underline', 'Bold,Italic',
                       'Bold,Underline', 'Italic,Underline',
                       'Bold,Italic,Underline'}
        
        if style not in valid_styles:
            return ValidationError(
                property_name=property_name,
                expected_value=f"One of {valid_styles}",
                actual_value=style,
                error_type="invalid_text_style"
            )
        
        return None
    
    @classmethod
    def validate_shape_style(
        cls,
        style: Dict[str, Any],
        available_fonts: Optional[List[str]] = None
    ) -> List[ValidationError]:
        """Validate all properties in a shape style"""
        errors = []
        
        # Validate colors
        for color_prop in ['fill_color', 'line_color', 'text_color']:
            if color_prop in style and style[color_prop]:
                if error := cls.validate_color(style[color_prop], color_prop):
                    errors.append(error)
        
        # Validate numeric properties
        if 'line_weight' in style and style['line_weight'] is not None:
            if error := cls.validate_numeric(
                style['line_weight'],
                'line_weight',
                min_value=0.0
            ):
                errors.append(error)
        
        if 'text_size' in style and style['text_size'] is not None:
            if error := cls.validate_numeric(
                style['text_size'],
                'text_size',
                min_value=1.0,
                max_value=720.0  # Maximum Visio font size
            ):
                errors.append(error)
        
        if 'opacity' in style and style['opacity'] is not None:
            if error := cls.validate_numeric(
                style['opacity'],
                'opacity',
                min_value=0.0,
                max_value=1.0
            ):
                errors.append(error)
        
        # Validate font
        if 'font_name' in style and style['font_name']:
            if error := cls.validate_font(
                style['font_name'],
                'font_name',
                available_fonts
            ):
                errors.append(error)
        
        # Validate text style
        if 'text_style' in style and style['text_style']:
            if error := cls.validate_text_style(style['text_style'], 'text_style'):
                errors.append(error)
        
        return errors

    @classmethod
    def convert_color_to_rgb(cls, color: str) -> str:
        """Convert any supported color format to RGB format"""
        # Already in RGB format
        if cls.RGB_PATTERN.match(color):
            return color
        
        # Convert HEX to RGB
        if cls.HEX_PATTERN.match(color):
            color = color.lstrip('#')
            r = int(color[0:2], 16)
            g = int(color[2:4], 16)
            b = int(color[4:6], 16)
            return f"{r},{g},{b}"
        
        # Convert HTML color name to RGB
        if color.lower() in cls.HTML_COLOR_NAMES:
            # This is a simplified mapping - in practice you'd want a complete mapping
            color_map = {
                'red': '255,0,0',
                'green': '0,255,0',
                'blue': '0,0,255',
                'black': '0,0,0',
                'white': '255,255,255',
                'yellow': '255,255,0',
                'purple': '128,0,128',
                'orange': '255,165,0',
                'gray': '128,128,128',
                'brown': '165,42,42',
                'pink': '255,192,203',
                'cyan': '0,255,255',
                'magenta': '255,0,255'
            }
            return color_map.get(color.lower(), '0,0,0')
        
        raise ValueError(f"Unsupported color format: {color}") 