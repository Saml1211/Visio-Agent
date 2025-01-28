"""
Data models for validation results and issues.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ValidationSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationLocation(BaseModel):
    """Location information for validation issues"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    element_id: Optional[str] = Field(None, description="ID of the affected element")
    
class ValidationIssue(BaseModel):
    """Detailed information about a validation issue"""
    code: str = Field(..., description="Unique issue code")
    message: str = Field(..., description="Human-readable issue description")
    severity: ValidationSeverity = Field(..., description="Issue severity level")
    location: Optional[ValidationLocation] = Field(None, description="Issue location")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class ColorValidationResult(BaseModel):
    """Results from color accessibility validation"""
    contrast_ratio: float = Field(..., description="Average contrast ratio")
    wcag_aa_pass: bool = Field(..., description="Meets WCAG AA standards")
    wcag_aaa_pass: bool = Field(..., description="Meets WCAG AAA standards")
    color_blind_safe: bool = Field(..., description="Safe for color blind users")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Color-related issues")

class TextValidationResult(BaseModel):
    """Results from text readability validation"""
    readability_score: float = Field(..., description="Overall readability score")
    font_valid: bool = Field(..., description="Font size and family are valid")
    size_valid: bool = Field(..., description="Text size meets requirements")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Text-related issues")

class SpacingValidationResult(BaseModel):
    """Results from element spacing validation"""
    spacing_score: float = Field(..., description="Overall spacing score")
    crowded_areas: List[Dict[str, Any]] = Field(default_factory=list, description="Areas with insufficient spacing")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Spacing-related issues")

class ValidationResult(BaseModel):
    """Comprehensive validation results"""
    passed: bool = Field(..., description="Overall validation passed")
    score: float = Field(..., description="Overall validation score (0-100)")
    color_results: ColorValidationResult = Field(..., description="Color validation results")
    text_results: TextValidationResult = Field(..., description="Text validation results")
    spacing_results: SpacingValidationResult = Field(..., description="Spacing validation results")
    issues: List[ValidationIssue] = Field(default_factory=list, description="All validation issues")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

# Request Models
class ColorValidationRequest(BaseModel):
    """Request model for color validation"""
    colors: List[Dict[str, str]] = Field(..., description="List of color pairs to validate")
    min_contrast: Optional[float] = Field(4.5, description="Minimum required contrast ratio")

class TextValidationRequest(BaseModel):
    """Request model for text validation"""
    text_elements: List[Dict[str, Any]] = Field(..., description="List of text elements to validate")
    min_size: Optional[float] = Field(8.0, description="Minimum font size")
    max_length: Optional[int] = Field(200, description="Maximum text length")

class SpacingValidationRequest(BaseModel):
    """Request model for spacing validation"""
    elements: List[Dict[str, Any]] = Field(..., description="List of elements to validate spacing")
    min_gap: Optional[float] = Field(20.0, description="Minimum gap between elements")
    max_density: Optional[float] = Field(0.7, description="Maximum element density")

class DiagramValidationRequest(BaseModel):
    """Request model for full diagram validation"""
    colors: List[Dict[str, str]] = Field(..., description="Color pairs to validate")
    text_elements: List[Dict[str, Any]] = Field(..., description="Text elements to validate")
    elements: List[Dict[str, Any]] = Field(..., description="Elements to validate spacing")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="Custom validation rules") 