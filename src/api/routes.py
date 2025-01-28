from fastapi import FastAPI, HTTPException, File, UploadFile, Body, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..services.deep_validator import (
    DeepValidator,
    ColorAccessibilityResult,
    TextReadabilityResult,
    SpacingResult,
    ValidationResult
)

app = FastAPI(
    title="Diagram Validation API",
    description="""
    API for validating diagrams against accessibility, readability, and design best practices.
    
    Features:
    - Color accessibility validation (WCAG compliance)
    - Text readability analysis
    - Element spacing validation
    - Comprehensive diagram validation
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

class ColorValidationRequest(BaseModel):
    """Request model for color validation"""
    foreground_color: tuple[int, int, int] = Field(
        ...,
        description="RGB values for foreground color",
        example=(0, 0, 0)
    )
    background_color: tuple[int, int, int] = Field(
        ...,
        description="RGB values for background color",
        example=(255, 255, 255)
    )
    min_contrast: Optional[float] = Field(
        4.5,
        description="Minimum required contrast ratio (WCAG AA: 4.5, AAA: 7.0)",
        ge=1.0,
        le=21.0
    )

class ColorValidationResponse(BaseModel):
    """Response model for color validation"""
    is_accessible: bool = Field(
        ...,
        description="Whether the color combination meets accessibility standards"
    )
    contrast_ratio: float = Field(
        ...,
        description="Calculated contrast ratio between colors"
    )
    wcag_level: str = Field(
        ...,
        description="WCAG compliance level (AAA, AA, or Fail)"
    )

class TextValidationRequest(BaseModel):
    """Request model for text validation"""
    text: str = Field(
        ...,
        description="Text to validate for readability",
        min_length=1
    )
    min_flesch_score: Optional[float] = Field(
        60.0,
        description="Minimum required Flesch Reading Ease score",
        ge=0.0,
        le=100.0
    )

class TextValidationResponse(BaseModel):
    """Response model for text validation"""
    is_readable: bool = Field(
        ...,
        description="Whether the text meets readability standards"
    )
    flesch_score: float = Field(
        ...,
        description="Calculated Flesch Reading Ease score"
    )
    grade_level: float = Field(
        ...,
        description="Calculated Flesch-Kincaid Grade Level"
    )
    issues: List[str] = Field(
        ...,
        description="List of identified readability issues"
    )

class SpacingValidationRequest(BaseModel):
    """Request model for element spacing validation"""
    elements: List[Dict[str, Any]] = Field(
        ...,
        description="List of diagram elements with position data"
    )
    min_spacing: Optional[float] = Field(
        10.0,
        description="Minimum required spacing between elements in pixels",
        ge=0.0
    )

class SpacingValidationResponse(BaseModel):
    """Response model for spacing validation"""
    is_sufficient: bool = Field(
        ...,
        description="Whether element spacing meets requirements"
    )
    min_spacing: float = Field(
        ...,
        description="Minimum spacing found between elements"
    )
    crowded_areas: List[Dict[str, Any]] = Field(
        ...,
        description="Details of areas with insufficient spacing"
    )

class DiagramValidationRequest(BaseModel):
    """Request model for full diagram validation"""
    elements: List[Dict[str, Any]] = Field(
        ...,
        description="List of diagram elements with properties"
    )
    validation_options: Optional[Dict[str, Any]] = Field(
        {},
        description="Optional validation parameters"
    )

class DiagramValidationResponse(BaseModel):
    """Response model for full diagram validation"""
    success: bool = Field(
        ...,
        description="Overall validation success"
    )
    issues: List[str] = Field(
        ...,
        description="List of validation issues found"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of validation"
    )
    details: Dict[str, Any] = Field(
        ...,
        description="Detailed validation results"
    )

@app.post(
    "/api/validate/colors",
    response_model=ColorValidationResponse,
    tags=["Validation"],
    summary="Validate color accessibility",
    description="""
    Validate color accessibility between foreground and background colors.
    
    Checks:
    - Contrast ratio calculation
    - WCAG 2.1 compliance (AA and AAA levels)
    - Minimum contrast requirements
    """
)
async def validate_colors(
    request: ColorValidationRequest
) -> ColorValidationResponse:
    """Validate color accessibility"""
    validator = DeepValidator()
    result = validator.validate_color_accessibility(
        request.foreground_color,
        request.background_color,
        request.min_contrast
    )
    
    return ColorValidationResponse(
        is_accessible=result.is_accessible,
        contrast_ratio=result.contrast_ratio,
        wcag_level=result.wcag_level
    )

@app.post(
    "/api/validate/text",
    response_model=TextValidationResponse,
    tags=["Validation"],
    summary="Validate text readability",
    description="""
    Validate text readability using multiple metrics.
    
    Checks:
    - Flesch Reading Ease score
    - Flesch-Kincaid Grade Level
    - Word and sentence length
    - Complex word usage
    """
)
async def validate_text(
    request: TextValidationRequest
) -> TextValidationResponse:
    """Validate text readability"""
    validator = DeepValidator()
    result = validator.validate_text_readability(
        request.text,
        request.min_flesch_score
    )
    
    return TextValidationResponse(
        is_readable=result.is_readable,
        flesch_score=result.flesch_score,
        grade_level=result.grade_level,
        issues=result.issues
    )

@app.post(
    "/api/validate/spacing",
    response_model=SpacingValidationResponse,
    tags=["Validation"],
    summary="Validate element spacing",
    description="""
    Validate spacing between diagram elements.
    
    Checks:
    - Minimum spacing requirements
    - Element overlap detection
    - Crowded area identification
    """
)
async def validate_spacing(
    request: SpacingValidationRequest
) -> SpacingValidationResponse:
    """Validate element spacing"""
    validator = DeepValidator()
    result = validator.validate_element_spacing(
        request.elements,
        request.min_spacing
    )
    
    return SpacingValidationResponse(
        is_sufficient=result.is_sufficient,
        min_spacing=result.min_spacing,
        crowded_areas=result.crowded_areas
    )

@app.post(
    "/api/validate/diagram",
    response_model=DiagramValidationResponse,
    tags=["Validation"],
    summary="Perform full diagram validation",
    description="""
    Perform comprehensive validation of a diagram.
    
    Validates:
    - Color accessibility
    - Text readability
    - Element spacing
    - Overall diagram structure
    
    Returns detailed results for all validation checks.
    """
)
async def validate_diagram(
    request: DiagramValidationRequest
) -> DiagramValidationResponse:
    """Validate entire diagram"""
    validator = DeepValidator()
    result = await validator.validate_diagram({
        'elements': request.elements,
        **request.validation_options
    })
    
    return DiagramValidationResponse(
        success=result.success,
        issues=result.issues,
        timestamp=datetime.now(),
        details={
            'color_results': [
                {
                    'is_accessible': r.is_accessible,
                    'contrast_ratio': r.contrast_ratio,
                    'wcag_level': r.wcag_level
                }
                for r in result.color_results
            ],
            'text_results': [
                {
                    'is_readable': r.is_readable,
                    'flesch_score': r.flesch_score,
                    'grade_level': r.grade_level,
                    'issues': r.issues
                }
                for r in result.text_results
            ],
            'spacing_result': {
                'is_sufficient': result.spacing_result.is_sufficient,
                'min_spacing': result.spacing_result.min_spacing,
                'crowded_areas': result.spacing_result.crowded_areas
            } if result.spacing_result else None
        }
    )

@app.get(
    "/api/health",
    tags=["System"],
    summary="Check API health",
    description="Check if the API is running and healthy"
)
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": app.version
    }

@app.get(
    "/api/metrics",
    tags=["System"],
    summary="Get API metrics",
    description="Get metrics about API usage and performance"
)
async def get_metrics() -> Dict[str, Any]:
    """Get API metrics"""
    # TODO: Implement metrics collection
    return {
        "requests_total": 0,
        "validation_count": 0,
        "error_count": 0,
        "average_response_time": 0.0
    } 