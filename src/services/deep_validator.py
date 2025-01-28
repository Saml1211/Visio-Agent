from typing import List, Dict, Optional, Union, Any, Tuple
from pydantic import BaseModel
from .exceptions import ValidationError
import logging
from wcag_contrast_ratio import rgb_to_luminance, contrast_ratio
from dataclasses import dataclass
from datetime import datetime
import asyncio
import gc
from contextlib import asynccontextmanager
import colorsys
import re
import math
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class TextElement(BaseModel):
    """Represents a text element in the diagram"""
    content: str
    font_size: int
    color: str
    background_color: str
    position: Dict[str, float]

class ValidationSeverity(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ValidationIssue(BaseModel):
    """Represents a validation issue found in the diagram"""
    message: str
    severity: ValidationSeverity
    location: Dict[str, Union[int, str]]
    element_id: Optional[str] = None

class ValidationResult(BaseModel):
    """Result of a single validation check"""
    passed: bool
    issues: List[ValidationIssue] = []

class ValidationReport(BaseModel):
    """Complete validation report for a diagram"""
    overall_status: str
    validation_results: List[ValidationResult]
    total_issues: int
    critical_issues: int
    timestamp: str

@dataclass
class ValidationResult:
    """Result of a validation check"""
    passed: bool
    issues: List[Dict[str, Any]]
    validation_time: datetime = datetime.now()

class ResourceManager:
    """Manages resources for validation operations"""
    def __init__(self):
        self.active_validations = 0
        self.max_concurrent = 5
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
    
    @asynccontextmanager
    async def validation_context(self):
        """Context manager for validation resources"""
        try:
            async with self._semaphore:
                async with self._lock:
                    self.active_validations += 1
                yield
        finally:
            async with self._lock:
                self.active_validations -= 1
                if self.active_validations == 0:
                    # Cleanup when no active validations
                    gc.collect()

@dataclass
class ColorAccessibilityResult:
    """Result of color accessibility validation"""
    is_accessible: bool
    contrast_ratio: float
    wcag_level: str  # 'AA', 'AAA', or 'Fail'
    foreground_color: Tuple[int, int, int]
    background_color: Tuple[int, int, int]

@dataclass
class TextReadabilityResult:
    """Result of text readability validation"""
    flesch_score: float
    grade_level: float
    is_readable: bool
    issues: List[str]

@dataclass
class SpacingResult:
    """Result of element spacing validation"""
    min_spacing: float
    is_sufficient: bool
    crowded_areas: List[Dict[str, Any]]

class DeepValidator:
    """Enhanced validator for diagram accessibility and best practices"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.resource_manager = ResourceManager()
        self._setup_logging()
        self._setup_validation_rules()
    
    def _setup_logging(self):
        """Configure logging"""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
    
    def _setup_validation_rules(self):
        """Initialize validation rules"""
        self.color_rules = {
            'min_contrast_normal': self.config.get('min_contrast_normal', 4.5),
            'min_contrast_large': self.config.get('min_contrast_large', 3.0),
            'max_colors': self.config.get('max_colors', 7)
        }
        
        self.text_rules = {
            'min_size_normal': self.config.get('min_size_normal', 8),
            'min_size_title': self.config.get('min_size_title', 10),
            'max_length_label': self.config.get('max_length_label', 50),
            'max_length_desc': self.config.get('max_length_desc', 200)
        }
        
        self.spacing_rules = {
            'min_gap': self.config.get('min_gap', 20),
            'group_threshold': self.config.get('group_threshold', 100),
            'max_density': self.config.get('max_density', 0.7)
        }
    
    async def validate_colors(
        self,
        colors: List[Dict[str, str]]
    ) -> ColorAccessibilityResult:
        """Validate color accessibility"""
        try:
            issues = []
            all_contrasts = []
            
            for color_pair in colors:
                fg = self._parse_color(color_pair['foreground'])
                bg = self._parse_color(color_pair['background'])
                
                if not fg or not bg:
                    issues.append(ValidationIssue(
                        code="COLOR_001",
                        message="Invalid color format",
                        severity=ValidationSeverity.ERROR,
                        context={'colors': color_pair}
                    ))
                    continue
                
                contrast = self._calculate_contrast(fg, bg)
                all_contrasts.append(contrast)
                
                if contrast < self.color_rules['min_contrast_normal']:
                    issues.append(ValidationIssue(
                        code="COLOR_002",
                        message=f"Insufficient contrast ratio: {contrast:.1f}",
                        severity=ValidationSeverity.ERROR,
                        context={
                            'contrast': contrast,
                            'colors': color_pair
                        }
                    ))
            
            return ColorAccessibilityResult(
                is_accessible=all(c >= self.color_rules['min_contrast_normal'] for c in all_contrasts),
                contrast_ratio=sum(all_contrasts) / len(all_contrasts) if all_contrasts else 0,
                wcag_level='AA' if all(c >= 7.0 for c in all_contrasts) else 'Fail',
                foreground_color=fg,
                background_color=bg
            )
            
        except Exception as e:
            logger.error(f"Color validation failed: {str(e)}")
            raise ValidationError(f"Color validation failed: {str(e)}")
    
    async def validate_text(
        self,
        text_elements: List[Dict[str, Any]]
    ) -> TextReadabilityResult:
        """Validate text readability"""
        try:
            issues = []
            readability_scores = []
            
            for element in text_elements:
                # Validate font size
                size = element.get('font_size', 0)
                if size < self.text_rules['min_size_normal']:
                    issues.append(ValidationIssue(
                        code="TEXT_001",
                        message=f"Font size too small: {size}pt",
                        severity=ValidationSeverity.WARNING,
                        context={'element': element}
                    ))
                
                # Validate text length
                content = element.get('content', '')
                if len(content) > self.text_rules['max_length_desc']:
                    issues.append(ValidationIssue(
                        code="TEXT_002",
                        message="Text content too long",
                        severity=ValidationSeverity.WARNING,
                        context={'element': element}
                    ))
                
                # Calculate readability score
                score = self._calculate_readability(content)
                readability_scores.append(score)
            
            return TextReadabilityResult(
                flesch_score=sum(readability_scores) / len(readability_scores) if readability_scores else 0,
                grade_level=self._calculate_grade_level(sum(readability_scores) / len(readability_scores) if readability_scores else 0),
                is_readable=sum(readability_scores) / len(readability_scores) >= 60,
                issues=issues
            )
            
        except Exception as e:
            logger.error(f"Text validation failed: {str(e)}")
            raise ValidationError(f"Text validation failed: {str(e)}")
    
    async def validate_spacing(
        self,
        elements: List[Dict[str, Any]]
    ) -> SpacingResult:
        """Validate element spacing"""
        try:
            issues = []
            crowded_areas = []
            
            # Check minimum spacing between elements
            for i, elem1 in enumerate(elements):
                for elem2 in elements[i+1:]:
                    distance = self._calculate_distance(elem1, elem2)
                    
                    if distance < self.spacing_rules['min_gap']:
                        crowded_areas.append({
                            'elements': [elem1.get('id'), elem2.get('id')],
                            'distance': distance
                        })
                        
                        issues.append(ValidationIssue(
                            code="SPACING_001",
                            message=f"Elements too close: {distance:.1f}px",
                            severity=ValidationSeverity.WARNING,
                            context={
                                'elements': [elem1, elem2],
                                'distance': distance
                            }
                        ))
            
            # Calculate overall spacing score
            total_area = self._calculate_total_area(elements)
            used_area = self._calculate_used_area(elements)
            density = used_area / total_area if total_area > 0 else 1
            
            if density > self.spacing_rules['max_density']:
                issues.append(ValidationIssue(
                    code="SPACING_002",
                    message="Diagram too dense",
                    severity=ValidationSeverity.WARNING,
                    context={'density': density}
                ))
            
            return SpacingResult(
                min_spacing=self.spacing_rules['min_gap'],
                is_sufficient=density <= self.spacing_rules['max_density'],
                crowded_areas=crowded_areas
            )
            
        except Exception as e:
            logger.error(f"Spacing validation failed: {str(e)}")
            raise ValidationError(f"Spacing validation failed: {str(e)}")
    
    async def validate_diagram(
        self,
        diagram_data: Dict[str, Any]
    ) -> ValidationResult:
        """Perform comprehensive diagram validation"""
        try:
            # Parallel validation
            color_result, text_result, spacing_result = await asyncio.gather(
                self.validate_colors(diagram_data.get('colors', [])),
                self.validate_text(diagram_data.get('text_elements', [])),
                self.validate_spacing(diagram_data.get('elements', []))
            )
            
            # Combine all issues
            all_issues = [
                *color_result.issues,
                *text_result.issues,
                *spacing_result.issues
            ]
            
            # Calculate overall score
            weights = {
                'color': 0.4,
                'text': 0.3,
                'spacing': 0.3
            }
            
            score = (
                color_result.contrast_ratio * weights['color'] +
                text_result.flesch_score * weights['text'] +
                (100 - spacing_result.crowded_areas.size() * 100 / len(diagram_data.get('elements', []))) * weights['spacing']
            )
            
            return ValidationResult(
                passed=len([i for i in all_issues if i.severity == ValidationSeverity.ERROR]) == 0,
                score=score,
                color_results=color_result,
                text_results=text_result,
                spacing_result=spacing_result,
                issues=all_issues,
                metadata={
                    'validation_time': datetime.now().isoformat(),
                    'validator_version': '1.0.0'
                }
            )
            
        except Exception as e:
            logger.error(f"Diagram validation failed: {str(e)}")
            raise ValidationError(f"Diagram validation failed: {str(e)}")
    
    def _parse_color(self, color: str) -> Optional[Tuple[int, int, int]]:
        """Parse color string to RGB tuple"""
        try:
            if color.startswith('#'):
                color = color[1:]
            if len(color) == 6:
                return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            return None
        except Exception:
            return None
    
    def _calculate_contrast(self, fg: Tuple[int, int, int], bg: Tuple[int, int, int]) -> float:
        """Calculate contrast ratio between two colors"""
        try:
            fg_lum = rgb_to_luminance(*fg)
            bg_lum = rgb_to_luminance(*bg)
            return contrast_ratio(fg_lum, bg_lum)
        except Exception:
            return 0
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate text readability score"""
        try:
            words = len(text.split())
            sentences = len(re.split(r'[.!?]+', text))
            if sentences == 0:
                return 0
            return min(100, (words / sentences) * 10)
        except Exception:
            return 0
    
    def _calculate_distance(self, elem1: Dict[str, Any], elem2: Dict[str, Any]) -> float:
        """Calculate distance between two elements"""
        try:
            x1, y1 = elem1.get('x', 0), elem1.get('y', 0)
            x2, y2 = elem2.get('x', 0), elem2.get('y', 0)
            return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        except Exception:
            return float('inf')
    
    def _calculate_total_area(self, elements: List[Dict[str, Any]]) -> float:
        """Calculate total diagram area"""
        try:
            if not elements:
                return 0
            xs = [e.get('x', 0) for e in elements]
            ys = [e.get('y', 0) for e in elements]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            return width * height
        except Exception:
            return 0
    
    def _calculate_used_area(self, elements: List[Dict[str, Any]]) -> float:
        """Calculate area used by elements"""
        try:
            return sum(
                e.get('width', 0) * e.get('height', 0)
                for e in elements
            )
        except Exception:
            return 0
    
    def _calculate_grade_level(self, flesch_score: float) -> float:
        """Calculate grade level based on Flesch Reading Ease score"""
        try:
            if flesch_score < 30:
                return 0
            elif flesch_score < 50:
                return 1
            elif flesch_score < 60:
                return 2
            elif flesch_score < 70:
                return 3
            elif flesch_score < 80:
                return 4
            else:
                return 5
        except Exception:
            return 0
