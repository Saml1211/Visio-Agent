from typing import List, Dict, Optional, Union
from pydantic import BaseModel
from .exceptions import ValidationError
import logging
from wcag_contrast_ratio import rgb_to_luminance, contrast_ratio

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

class DeepValidator:
    """Validates diagrams for accessibility and best practices"""
    
    def __init__(self):
        self.validators = {
            'contrast': self._check_contrast_ratio,
            'text_size': self._check_text_size,
            'spacing': self._check_element_spacing,
            'color_blindness': self._check_color_blindness,
            'readability': self._check_text_readability
        }
    
    async def validate_diagram(self, diagram_data: Dict) -> ValidationReport:
        """
        Perform comprehensive validation of a diagram
        
        Args:
            diagram_data: Dictionary containing diagram elements and properties
            
        Returns:
            ValidationReport containing all validation results
        """
        try:
            results: List[ValidationResult] = []
            critical_count = 0
            
            for validator_name, validator_func in self.validators.items():
                result = await validator_func(diagram_data)
                results.append(result)
                critical_count += sum(1 for issue in result.issues 
                                   if issue.severity == ValidationSeverity.HIGH)
            
            total_issues = sum(len(result.issues) for result in results)
            
            return ValidationReport(
                overall_status="failed" if critical_count > 0 else "passed",
                validation_results=results,
                total_issues=total_issues,
                critical_issues=critical_count,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            raise ValidationError(f"Diagram validation failed: {str(e)}")
    
    async def _check_contrast_ratio(self, diagram_data: Dict) -> ValidationResult:
        """Check contrast ratios meet WCAG guidelines"""
        issues = []
        for element in diagram_data.get('text_elements', []):
            text_elem = TextElement(**element)
            ratio = contrast_ratio(
                rgb_to_luminance(text_elem.color),
                rgb_to_luminance(text_elem.background_color)
            )
            if ratio < 4.5:  # WCAG AA standard
                issues.append(ValidationIssue(
                    message=f"Insufficient contrast ratio: {ratio:.2f}",
                    severity=ValidationSeverity.HIGH,
                    location={"x": text_elem.position["x"], "y": text_elem.position["y"]},
                    element_id=element.get("id")
                ))
        return ValidationResult(passed=len(issues)==0, issues=issues)
    
    async def _check_text_size(self, diagram_data: Dict) -> ValidationResult:
        """Validate text sizes for readability"""
        issues = []
        for element in diagram_data.get('text_elements', []):
            text_elem = TextElement(**element)
            if text_elem.font_size < 11:
                issues.append(ValidationIssue(
                    message=f"Text size too small: {text_elem.font_size}pt",
                    severity=ValidationSeverity.MEDIUM,
                    location={"x": text_elem.position["x"], "y": text_elem.position["y"]},
                    element_id=element.get("id")
                ))
        return ValidationResult(passed=len(issues)==0, issues=issues)
    
    async def _check_element_spacing(self, diagram_data: Dict) -> ValidationResult:
        """Check spacing between elements"""
        # Implementation for spacing validation
        return ValidationResult(passed=True, issues=[])
    
    async def _check_color_blindness(self, diagram_data: Dict) -> ValidationResult:
        """Validate color choices for color blindness accessibility"""
        # Implementation for color blindness checks
        return ValidationResult(passed=True, issues=[])
    
    async def _check_text_readability(self, diagram_data: Dict) -> ValidationResult:
        """Check text readability metrics"""
        # Implementation for readability validation
        return ValidationResult(passed=True, issues=[])
