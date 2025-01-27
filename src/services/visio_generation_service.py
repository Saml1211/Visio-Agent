import logging
from typing import Dict, List, Optional, Any, Union, Tuple, Set, Callable
from dataclasses import dataclass, field
from pathlib import Path
import win32com.client
import pythoncom
import os
import tempfile
import subprocess
from .ai_service_config import AIServiceManager
from enum import Enum, auto
import math
import time
import sys

from .file_cache_service import FileCacheService
from .exceptions import VisioError, VisioGenerationError
from .visio_generation.shape_validation import ShapePropertyValidator, ValidationError
from .visio_style_guide_service import VisioStyleGuideService
from models.visio_style_models import FontRules, ShapeRules, LineRules, RGBColor
from .integrations.tech_specs_service import TechSpecsService
from .integrations.screenpipe_adapter import ScreenPipeAdapter
from .integrations.spec_search import SpecSearch
from .connector_routing import ConnectorRouter
from .visio.config import ShapeConfig, ConnectorConfig
from .connector_router import OrthogonalRouter, CurvedRouter, StraightRouter
from .routing import OrthogonalRouter, CurvedRouter
from .ai_layout_adviser import AILayoutAdviser
from .connector_routing import HybridRouter, AIRoutingConfig, RoutingConstraints

logger = logging.getLogger(__name__)

class ConnectorStyle(str, Enum):
    """Connector line styles"""
    STRAIGHT = "straight"
    RIGHT_ANGLE = "right_angle"
    CURVED = "curved"

class ConnectorRouting(str, Enum):
    """Connector routing algorithms supported by Visio"""
    SHORTEST_PATH = "shortest_path"      # visAutoRouteStraight (0)
    AVOID_SHAPES = "avoid_shapes"        # visAutoRouteCenter (1)
    NETWORK_FLOW = "network_flow"        # Custom implementation
    HIERARCHICAL_TB = "hierarchical_tb"  # visAutoRouteFlowchartSN (2)
    HIERARCHICAL_LR = "hierarchical_lr"  # visAutoRouteFlowchartWE (3)
    TREE = "tree"                        # visAutoRouteTree (4)

class ConnectionPoint(str, Enum):
    """Connection point locations on shapes"""
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    CENTER = "center"

class InternalShapeType(str, Enum):
    """Types of internal shapes supported"""
    RECTANGLE = "rectangle"
    ELLIPSE = "ellipse"
    DIAMOND = "diamond"
    HEXAGON = "hexagon"
    TEXT = "text"

@dataclass
class VisioShape:
    """Represents a shape in a Visio diagram"""
    shape_type: str
    name: str
    x: float
    y: float
    width: float = 1.0
    height: float = 1.0
    text: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    connections: Optional[List[Dict[str, Any]]] = None

@dataclass
class VisioDocument:
    """Represents a Visio document"""
    template_path: str
    shapes: List[VisioShape]
    page_width: float = 11.0
    page_height: float = 8.5
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Point:
    """2D point representation"""
    x: float
    y: float

@dataclass
class CustomConnectionPoint:
    """Custom connection point with relative positioning"""
    name: str
    relative_x: float  # 0.0 to 1.0 relative to shape width
    relative_y: float  # 0.0 to 1.0 relative to shape height
    angle: Optional[float] = None  # Connection angle in degrees (0-359)

@dataclass
class ShapeStyle:
    """Style configuration for shapes"""
    fill_color: Optional[str] = None          # RGB color string
    fill_transparency: Optional[int] = None   # 0-100
    line_color: Optional[str] = None          # RGB color string
    line_weight: Optional[float] = None       # Points
    line_pattern: Optional[int] = None        # 0-solid, 1-dash, 2-dot, etc.
    text_color: Optional[str] = None          # RGB color string
    text_size: Optional[float] = None         # Points
    text_style: Optional[str] = None          # Bold, Italic, etc.
    rounding: Optional[float] = None          # Corner rounding (0.0-1.0)

@dataclass
class InternalShape:
    """Represents an internal shape within a grouped shape"""
    name: str
    relative_x: float
    relative_y: float
    width: float = 1.0
    height: float = 0.5
    shape_type: InternalShapeType = InternalShapeType.RECTANGLE
    text: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    connection_points: Optional[List[Union[ConnectionPoint, CustomConnectionPoint]]] = None
    style: Optional[ShapeStyle] = None

@dataclass
class DynamicContent:
    """Dynamic content configuration for shapes"""
    hyperlink: Optional[str] = None
    tooltip: Optional[str] = None
    hover_text: Optional[str] = None
    custom_properties: Optional[Dict[str, Any]] = None

@dataclass
class DynamicText:
    """Configuration for LLM-generated text"""
    prompt_template: str
    context: Dict[str, Any]
    max_length: Optional[int] = None
    style: Optional[str] = None  # e.g., "technical", "descriptive", "concise"

@dataclass
class PageConfig:
    """Configuration for a Visio page"""
    name: str
    width: float = 11.0
    height: float = 8.5
    background: Optional[str] = None
    header: Optional[str] = None
    footer: Optional[str] = None
    shapes: List[ShapeConfig] = field(default_factory=list)
    connectors: List[ConnectorConfig] = field(default_factory=list)

@dataclass
class ShapeConfig:
    """Configuration for a Visio shape"""
    master_name: str
    position: Point
    size: Optional[Tuple[float, float]] = None
    text: Optional[str] = None
    properties: Optional[Dict] = None
    internal_shapes: Optional[List[InternalShape]] = None
    dynamic_content: Optional[DynamicContent] = None  # Added field
    dynamic_text: Optional[DynamicText] = None  # Added field
    validation_rules: Optional[Dict[str, Any]] = None  # Added field

@dataclass
class ConnectorConfig:
    """Configuration for a Visio connector"""
    from_shape: str  # Shape ID or name
    to_shape: str    # Shape ID or name
    from_internal: Optional[str] = None  # Name of internal shape to connect from
    to_internal: Optional[str] = None    # Name of internal shape to connect to
    from_connection_point: Optional[ConnectionPoint] = None
    to_connection_point: Optional[ConnectionPoint] = None
    style: ConnectorStyle = ConnectorStyle.RIGHT_ANGLE
    routing: ConnectorRouting = ConnectorRouting.AVOID_SHAPES
    color: Optional[str] = None
    thickness: Optional[float] = None
    pattern: Optional[str] = None
    begin_arrow: Optional[str] = None
    end_arrow: Optional[str] = None

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()

@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    message: str
    severity: ValidationSeverity
    shape_id: Optional[str] = None
    page_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class ValidationResult:
    """Result of a validation check"""
    issues: List[ValidationIssue]
    is_valid: bool
    validation_time: float
    metadata: Optional[Dict[str, Any]] = None

class ValidationRule:
    """Base class for validation rules"""
    def __init__(
        self,
        name: str,
        description: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR
    ):
        self.name = name
        self.description = description
        self.severity = severity
    
    def validate(
        self,
        shape: any,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ValidationIssue]:
        """Validate a shape against this rule"""
        raise NotImplementedError

class RequiredPropertyRule(ValidationRule):
    """Rule to check for required properties"""
    def __init__(
        self,
        property_name: str,
        description: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR
    ):
        super().__init__(
            name=f"required_property_{property_name}",
            description=description,
            severity=severity
        )
        self.property_name = property_name
    
    def validate(
        self,
        shape: any,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ValidationIssue]:
        try:
            if not shape.Cells(self.property_name).Result(""):
                return ValidationIssue(
                    message=f"Missing required property: {self.property_name}",
                    severity=self.severity,
                    shape_id=shape.ID,
                    context={"property": self.property_name}
                )
        except:
            return ValidationIssue(
                message=f"Failed to check property: {self.property_name}",
                severity=self.severity,
                shape_id=shape.ID,
                context={"property": self.property_name}
            )
        return None

class CustomValidationRule(ValidationRule):
    """Rule with custom validation logic"""
    def __init__(
        self,
        name: str,
        description: str,
        validation_func: Callable[[any, Optional[Dict[str, Any]]], bool],
        error_message: str,
        severity: ValidationSeverity = ValidationSeverity.ERROR
    ):
        super().__init__(name=name, description=description, severity=severity)
        self.validation_func = validation_func
        self.error_message = error_message
    
    def validate(
        self,
        shape: any,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ValidationIssue]:
        if not self.validation_func(shape, context):
            return ValidationIssue(
                message=self.error_message,
                severity=self.severity,
                shape_id=shape.ID,
                context=context
            )
        return None

class VisioGenerationService:
    """Service for generating Visio diagrams with advanced connection routing"""
    
    def __init__(self):
        if sys.platform != "win32":
            raise VisioGenerationError("Visio service requires Windows")
        self.tech_specs = TechSpecsService()
        self.screenpipe = ScreenPipeAdapter()
        self.spec_search = SpecSearch()
        self.router = ConnectorRouter()
        self._visio_app = None

    async def initialize(self):
        """Initialize Visio application"""
        try:
            pythoncom.CoInitialize()
            self._visio_app = win32com.client.Dispatch("Visio.Application")
            self._visio_app.Visible = True
        except Exception as e:
            logger.error(f"Failed to initialize Visio: {str(e)}")
            raise VisioGenerationError(f"Visio initialization failed: {str(e)}")

    async def generate_diagram(self, components: List[Dict], layout: str = "auto") -> str:
        """Generate a Visio diagram from components"""
        try:
            if not self._visio_app:
                await self.initialize()

            doc = self._visio_app.Documents.Add("")
            page = doc.Pages.Item(1)

            # Create shapes
            shapes = await self._create_shapes(page, components)
            
            # Route connectors
            await self._create_connectors(page, shapes)

            # Apply layout
            if layout == "auto":
                page.Layout()

            return doc.FullName
        except Exception as e:
            logger.error(f"Diagram generation failed: {str(e)}")
            raise VisioGenerationError(f"Failed to generate diagram: {str(e)}")

    async def _create_shapes(self, page: any, components: List[Dict]) -> Dict[str, any]:
        shapes = {}
        for comp in components:
            try:
                shape_config = ShapeConfig(
                    id=comp["id"],
                    type=comp["type"],
                    position=comp.get("position", {"x": 0, "y": 0}),
                    size=comp.get("size", {"width": 2, "height": 1}),
                    style=comp.get("style", {}),
                    text=comp.get("label")
                )
                
                shape = page.Drop(
                    self._get_master(shape_config.type),
                    shape_config.position["x"],
                    shape_config.position["y"]
                )
                
                if shape_config.text:
                    shape.Text = shape_config.text
                    
                shapes[shape_config.id] = shape
            except Exception as e:
                logger.error(f"Failed to create shape {comp.get('id')}: {str(e)}")
                raise VisioGenerationError(f"Shape creation failed: {str(e)}")
                
        return shapes

    async def _create_connectors(self, page: any, shapes: Dict[str, any]):
        try:
            connections = await self.router.get_optimal_routing(shapes)
            for conn in connections:
                config = ConnectorConfig(
                    id=conn["id"],
                    source_id=conn["source"],
                    target_id=conn["target"],
                    routing_style=conn.get("style", "straight"),
                    points=conn.get("points", []),
                    style=conn.get("line_style", {})
                )
                
                connector = page.Drop(
                    self._get_connector_master(config.routing_style),
                    0, 0
                )
                
                connector.ConnectShapes(
                    shapes[config.source_id],
                    shapes[config.target_id]
                )
        except Exception as e:
            logger.error(f"Failed to create connectors: {str(e)}")
            raise VisioGenerationError(f"Connector creation failed: {str(e)}")

    def _get_master(self, shape_type: str) -> any:
        """Get Visio master shape by type"""
        try:
            stencil = self._visio_app.Documents.OpenStencil("BASIC_U.VSS")
            return stencil.Masters.ItemU(shape_type)
        except Exception as e:
            logger.error(f"Failed to get master shape: {str(e)}")
            raise VisioGenerationError(f"Master shape not found: {str(e)}")

    def _get_connector_master(self, style: str) -> any:
        """Get connector master based on style"""
        try:
            stencil = self._visio_app.Documents.OpenStencil("CONNEC_U.VSS")
            return stencil.Masters.ItemU("Dynamic connector")
        except Exception as e:
            logger.error(f"Failed to get connector master: {str(e)}")
            raise VisioGenerationError(f"Connector master not found: {str(e)}")

    async def cleanup(self):
        """Clean up Visio resources"""
        try:
            if self._visio_app:
                self._visio_app.Quit()
                pythoncom.CoUninitialize()
        except Exception as e:
            logger.error(f"Failed to cleanup Visio: {str(e)}")

    def add_validation_rule(
        self,
        rule: ValidationRule,
        category: str = "default"
    ) -> None:
        """Add a validation rule"""
        if category not in self.validation_rules:
            self.validation_rules[category] = []
        self.validation_rules[category].append(rule)
    
    async def validate_diagram(
        self,
        doc: any,
        categories: Optional[Set[str]] = None,
        custom_rules: Optional[List[ValidationRule]] = None
    ) -> ValidationResult:
        """
        Validate a Visio diagram
        
        Args:
            doc: Visio document to validate
            categories: Optional set of rule categories to apply
            custom_rules: Optional list of additional rules to apply
            
        Returns:
            ValidationResult containing any issues found
        """
        try:
            start_time = time.time()
            issues: List[ValidationIssue] = []
            
            # Get rules to apply
            rules = []
            if categories:
                for category in categories:
                    rules.extend(self.validation_rules.get(category, []))
            else:
                rules.extend(self.validation_rules["default"])
            
            if custom_rules:
                rules.extend(custom_rules)
            
            # Validate each page
            for page in doc.Pages:
                page_issues = await self._validate_page(page, rules)
                issues.extend(page_issues)
            
            validation_time = time.time() - start_time
            is_valid = not any(
                issue.severity == ValidationSeverity.ERROR for issue in issues
            )
            
            return ValidationResult(
                issues=issues,
                is_valid=is_valid,
                validation_time=validation_time,
                metadata={
                    "total_pages": doc.Pages.Count,
                    "total_shapes": sum(page.Shapes.Count for page in doc.Pages),
                    "rules_applied": len(rules)
                }
            )
            
        except Exception as e:
            logger.error(f"Error validating diagram: {str(e)}")
            return ValidationResult(
                issues=[ValidationIssue(
                    message=f"Validation failed: {str(e)}",
                    severity=ValidationSeverity.ERROR
                )],
                is_valid=False,
                validation_time=time.time() - start_time
            )
    
    async def _validate_page(
        self,
        page: any,
        rules: List[ValidationRule]
    ) -> List[ValidationIssue]:
        """Validate a single page"""
        issues = []
        
        try:
            # Validate each shape
            for shape in page.Shapes:
                shape_context = {
                    "page_name": page.Name,
                    "shape_type": shape.Type,
                    "master_name": shape.Master.NameU if shape.Master else None
                }
                
                for rule in rules:
                    issue = rule.validate(shape, shape_context)
                    if issue:
                        issue.page_name = page.Name
                        issues.append(issue)
            
            # Validate page-level requirements
            if not page.Shapes.Count:
                issues.append(ValidationIssue(
                    message="Page is empty",
                    severity=ValidationSeverity.WARNING,
                    page_name=page.Name
                ))
            
        except Exception as e:
            logger.error(f"Error validating page {page.Name}: {str(e)}")
            issues.append(ValidationIssue(
                message=f"Page validation failed: {str(e)}",
                severity=ValidationSeverity.ERROR,
                page_name=page.Name
            ))
        
        return issues

    def _add_shape(self, page: any, config: ShapeConfig) -> Tuple[any, Dict[str, any]]:
        """
        Add a shape to the page with specified configuration
        
        Returns:
            Tuple of (main shape, dict of internal shapes by name)
        """
        try:
            # Get master from document stencils
            master = None
            for stencil in page.Document.Masters:
                if stencil.NameU == config.master_name:
                    master = stencil
                    break
            
            if not master:
                raise VisioError(f"Master shape not found: {config.master_name}")
            
            # Drop main shape on page
            main_shape = page.Drop(master, config.position.x, config.position.y)
            
            # Set size if specified
            if config.size:
                main_shape.Cells("Width").FormulaU = f"{config.size[0]} in"
                main_shape.Cells("Height").FormulaU = f"{config.size[1]} in"
            
            # Set text if specified
            if config.text:
                main_shape.Text = config.text
            
            # Set additional properties
            if config.properties:
                for prop, value in config.properties.items():
                    try:
                        main_shape.Cells(prop).FormulaU = str(value)
                    except Exception as e:
                        logger.warning(
                            f"Failed to set property {prop} on shape: {str(e)}"
                        )
            
            internal_shapes = {}
            
            # Add internal shapes if specified
            if config.internal_shapes:
                # Create a group shape
                group = page.DrawRectangle(
                    config.position.x,
                    config.position.y,
                    config.position.x + (config.size[0] if config.size else 1.0),
                    config.position.y + (config.size[1] if config.size else 1.0)
                )
                group.Cells("FillPattern").FormulaU = "0"  # No fill
                group.Cells("LinePattern").FormulaU = "0"  # No line
                
                # Add internal shapes
                for internal in config.internal_shapes:
                    # Calculate absolute position
                    abs_x = config.position.x + internal.relative_x
                    abs_y = config.position.y + internal.relative_y
                    
                    # Create internal shape based on type
                    shape = None
                    if internal.shape_type == InternalShapeType.RECTANGLE:
                        shape = page.DrawRectangle(
                            abs_x, abs_y,
                            abs_x + internal.width,
                            abs_y + internal.height
                        )
                    elif internal.shape_type == InternalShapeType.ELLIPSE:
                        shape = page.DrawOval(
                            abs_x, abs_y,
                            abs_x + internal.width,
                            abs_y + internal.height
                        )
                    elif internal.shape_type == InternalShapeType.DIAMOND:
                        shape = page.DrawQuarterArc(
                            abs_x, abs_y,
                            abs_x + internal.width,
                            abs_y + internal.height,
                            0  # Diamond orientation
                        )
                    elif internal.shape_type == InternalShapeType.HEXAGON:
                        points = self._calculate_hexagon_points(
                            abs_x, abs_y, internal.width, internal.height
                        )
                        shape = page.DrawPolyline(
                            points + points[:2],  # Close the polygon
                            True  # Closed
                        )
                    elif internal.shape_type == InternalShapeType.TEXT:
                        shape = page.DrawRectangle(
                            abs_x, abs_y,
                            abs_x + internal.width,
                            abs_y + internal.height
                        )
                        shape.Cells("LinePattern").FormulaU = "0"  # No line
                    
                    # Set text and basic properties
                    shape.Text = internal.text or ""
                    shape.Cells("FillPattern").FormulaU = "0"  # No fill
                    
                    # Apply style if specified
                    if internal.style:
                        self._apply_shape_style(shape, internal.style)
                    
                    # Add connection points
                    if internal.connection_points:
                        for point in internal.connection_points:
                            self._add_connection_point(shape, point)
                    
                    # Set additional properties
                    if internal.properties:
                        for prop, value in internal.properties.items():
                            try:
                                shape.Cells(prop).FormulaU = str(value)
                            except Exception as e:
                                logger.warning(
                                    f"Failed to set property {prop} on internal shape: {str(e)}"
                                )
                    
                    internal_shapes[internal.name] = shape
                
                # Group all shapes
                shapes_to_group = [group] + list(internal_shapes.values())
                group = page.CreateSelection(
                    2,  # visSelect objects
                    0,  # visSelModeSkipSuper
                    *shapes_to_group
                )
                group = page.Application.Selection.Group()
                
                return group, internal_shapes
            
            return main_shape, internal_shapes
            
        except Exception as e:
            logger.error(f"Error adding shape: {str(e)}")
            raise VisioError(f"Failed to add shape: {str(e)}")
    
    def _add_connection_point(
        self, shape: any, point: Union[ConnectionPoint, CustomConnectionPoint]
    ) -> None:
        """Add a connection point to a shape at the specified location"""
        try:
            if isinstance(point, ConnectionPoint):
                # Handle predefined connection points
                if point == ConnectionPoint.LEFT:
                    shape.CellsSRC(7, 0, 0).FormulaU = "0"      # X position
                    shape.CellsSRC(7, 0, 1).FormulaU = "0.5"    # Y position
                    if shape.CellsSRC(7, 0, 4).Exists:  # Check if angle cell exists
                        shape.CellsSRC(7, 0, 4).FormulaU = "180deg"  # West
                elif point == ConnectionPoint.RIGHT:
                    shape.CellsSRC(7, 0, 0).FormulaU = "1"
                    shape.CellsSRC(7, 0, 1).FormulaU = "0.5"
                    if shape.CellsSRC(7, 0, 4).Exists:
                        shape.CellsSRC(7, 0, 4).FormulaU = "0deg"    # East
                elif point == ConnectionPoint.TOP:
                    shape.CellsSRC(7, 0, 0).FormulaU = "0.5"
                    shape.CellsSRC(7, 0, 1).FormulaU = "1"
                    if shape.CellsSRC(7, 0, 4).Exists:
                        shape.CellsSRC(7, 0, 4).FormulaU = "90deg"   # North
                elif point == ConnectionPoint.BOTTOM:
                    shape.CellsSRC(7, 0, 0).FormulaU = "0.5"
                    shape.CellsSRC(7, 0, 1).FormulaU = "0"
                    if shape.CellsSRC(7, 0, 4).Exists:
                        shape.CellsSRC(7, 0, 4).FormulaU = "270deg"  # South
                elif point == ConnectionPoint.CENTER:
                    shape.CellsSRC(7, 0, 0).FormulaU = "0.5"
                    shape.CellsSRC(7, 0, 1).FormulaU = "0.5"
            else:
                # Handle custom connection point
                shape.CellsSRC(7, 0, 0).FormulaU = str(point.relative_x)
                shape.CellsSRC(7, 0, 1).FormulaU = str(point.relative_y)
                if point.angle is not None and shape.CellsSRC(7, 0, 4).Exists:
                    shape.CellsSRC(7, 0, 4).FormulaU = f"{point.angle}deg"
        except Exception as e:
            logger.warning(f"Failed to add connection point: {str(e)}")
    
    def _calculate_hexagon_points(
        self, x: float, y: float, width: float, height: float
    ) -> List[Tuple[float, float]]:
        """Calculate points for a hexagon shape"""
        w = width / 2
        h = height / 2
        cx = x + w
        cy = y + h
        
        points = [
            (cx - w, cy),           # Left
            (cx - w/2, cy - h),     # Top left
            (cx + w/2, cy - h),     # Top right
            (cx + w, cy),           # Right
            (cx + w/2, cy + h),     # Bottom right
            (cx - w/2, cy + h),     # Bottom left
        ]
        return points
    
    def _apply_shape_style(self, shape: any, style: Dict[str, Any]) -> None:
        """Apply style properties to a Visio shape with validation.
        
        Args:
            shape: The Visio shape object to style
            style: Dictionary of style properties to apply
            
        Raises:
            VisioGenerationError: If validation fails or style cannot be applied
        """
        try:
            # Validate all style properties before applying
            validation_errors = ShapePropertyValidator.validate_shape_style(
                style,
                available_fonts=self._get_available_fonts()
            )
            
            if validation_errors:
                error_details = "\n".join(
                    f"{e.property_name}: {e.error_type} - {e.details}"
                    for e in validation_errors
                )
                raise VisioGenerationError(
                    f"Invalid shape style properties:\n{error_details}"
                )
            
            # Convert colors to RGB format for Visio
            if "fill_color" in style:
                style["fill_color"] = ShapePropertyValidator.convert_color_to_rgb(
                    style["fill_color"]
                )
            if "line_color" in style:
                style["line_color"] = ShapePropertyValidator.convert_color_to_rgb(
                    style["line_color"]
                )
            if "text_color" in style:
                style["text_color"] = ShapePropertyValidator.convert_color_to_rgb(
                    style["text_color"]
                )
            
            # Apply validated styles
            for prop, value in style.items():
                try:
                    if prop == "fill_color":
                        r, g, b = map(int, value.split(","))
                        shape.FillForegnd = self._rgb_to_visio_color(r, g, b)
                        
                    elif prop == "line_color":
                        r, g, b = map(int, value.split(","))
                        shape.LineColor = self._rgb_to_visio_color(r, g, b)
                        
                    elif prop == "text_color":
                        r, g, b = map(int, value.split(","))
                        shape.CharColor = self._rgb_to_visio_color(r, g, b)
                        
                    elif prop == "line_weight":
                        shape.LineWeight = float(value)
                        
                    elif prop == "text_size":
                        shape.CharSize = str(value) + " pt"
                        
                    elif prop == "opacity":
                        shape.FillForegndTrans = 1.0 - float(value)
                        
                    elif prop == "font_name":
                        shape.CharFont = value
                        
                    elif prop == "text_style":
                        self._apply_text_style(shape, value)
                        
                    logging.debug(f"Applied style property {prop}={value} to shape")
                    
                except Exception as e:
                    raise VisioGenerationError(
                        f"Failed to apply style property {prop}={value}: {str(e)}"
                    )
                
        except Exception as e:
            raise VisioGenerationError(f"Error applying shape style: {str(e)}")

    def _apply_text_style(self, shape: any, style_str: str) -> None:
        """Apply text style properties to a shape.
        
        Args:
            shape: The Visio shape object
            style_str: Comma-separated string of style properties
            
        Raises:
            VisioGenerationError: If style cannot be applied
        """
        try:
            styles = {s.strip().lower() for s in style_str.split(",")}
            
            shape.CharStyle = 0  # Reset style
            if "bold" in styles:
                shape.CharStyle = shape.CharStyle | 1
            if "italic" in styles:
                shape.CharStyle = shape.CharStyle | 2
            if "underline" in styles:
                shape.CharStyle = shape.CharStyle | 4
            
            logging.debug(f"Applied text styles {styles} to shape")
            
        except Exception as e:
            raise VisioGenerationError(f"Failed to apply text style {style_str}: {str(e)}")

    def _get_available_fonts(self) -> List[str]:
        """Get list of available fonts in Visio.
        
        Returns:
            List of font names available in Visio
        """
        try:
            fonts = self._visio_app.Fonts
            return [font.Name for font in fonts]
        except Exception as e:
            logging.warning(f"Failed to get available fonts: {str(e)}")
            return []  # Return empty list if fonts cannot be retrieved

    def _rgb_to_visio_color(self, r: int, g: int, b: int) -> int:
        """Convert RGB color values to Visio color format.
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            
        Returns:
            Visio color value
        """
        return r + (g * 256) + (b * 65536)

    def _add_connector(
        self,
        page: any,
        from_shape: any,
        to_shape: any,
        from_internal_shapes: Dict[str, any],
        to_internal_shapes: Dict[str, any],
        config: ConnectorConfig
    ) -> any:
        """Add a connector between shapes with specified configuration"""
        try:
            # Create connector
            connector = page.Drop(
                page.Document.Masters.ItemU("Dynamic connector"),
                0, 0
            )
            
            # Determine source and target shapes
            source = (
                from_internal_shapes.get(config.from_internal)
                if config.from_internal
                else from_shape
            )
            target = (
                to_internal_shapes.get(config.to_internal)
                if config.to_internal
                else to_shape
            )
            
            if config.from_internal and not source:
                raise VisioError(f"Internal shape not found: {config.from_internal}")
            if config.to_internal and not target:
                raise VisioError(f"Internal shape not found: {config.to_internal}")
            
            # Get connection points based on configuration
            source_cell = self._get_connection_cell(source, config.from_connection_point)
            target_cell = self._get_connection_cell(target, config.to_connection_point)
            
            # Set begin and end points
            connector.Cells("BeginX").GlueTo(source_cell)
            connector.Cells("EndX").GlueTo(target_cell)
            
            # Set routing style and algorithm
            if config.style == ConnectorStyle.RIGHT_ANGLE:
                connector.Cells("RouteStyle").FormulaU = "16"
            elif config.style == ConnectorStyle.CURVED:
                connector.Cells("RouteStyle").FormulaU = "2"
            
            # Apply routing algorithm
            if config.routing == ConnectorRouting.SHORTEST_PATH:
                connector.AutoRoute = 0  # visAutoRouteStraight
            elif config.routing == ConnectorRouting.AVOID_SHAPES:
                connector.AutoRoute = 1  # visAutoRouteCenter
            elif config.routing == ConnectorRouting.HIERARCHICAL_TB:
                connector.AutoRoute = 2  # visAutoRouteFlowchartSN
            elif config.routing == ConnectorRouting.HIERARCHICAL_LR:
                connector.AutoRoute = 3  # visAutoRouteFlowchartWE
            elif config.routing == ConnectorRouting.TREE:
                connector.AutoRoute = 4  # visAutoRouteTree
            elif config.routing == ConnectorRouting.NETWORK_FLOW:
                self._apply_network_flow_routing(connector, page)
            
            # Set appearance
            if config.color:
                connector.Cells("LineColor").FormulaU = f"RGB({config.color})"
            if config.thickness:
                connector.Cells("LineWeight").FormulaU = f"{config.thickness} pt"
            if config.pattern:
                connector.Cells("LinePattern").FormulaU = config.pattern
            if config.begin_arrow:
                connector.Cells("BeginArrow").FormulaU = config.begin_arrow
            if config.end_arrow:
                connector.Cells("EndArrow").FormulaU = config.end_arrow
            
            return connector
            
        except Exception as e:
            logger.error(f"Error adding connector: {str(e)}")
            raise VisioError(f"Failed to add connector: {str(e)}")
    
    def _get_connection_cell(
        self, shape: any, point: Optional[ConnectionPoint]
    ) -> any:
        """Get the appropriate connection cell based on the connection point"""
        if not point or point == ConnectionPoint.CENTER:
            return shape.Cells("PinX")
        
        # Map connection points to cell references
        point_map = {
            ConnectionPoint.LEFT: "Connections.X1",
            ConnectionPoint.RIGHT: "Connections.X2",
            ConnectionPoint.TOP: "Connections.X3",
            ConnectionPoint.BOTTOM: "Connections.X4"
        }
        
        return shape.Cells(point_map.get(point, "PinX"))
    
    def _apply_network_flow_routing(self, connector: any, page: any) -> None:
        """Apply network flow based routing algorithm to minimize crossings"""
        try:
            # Get all connectors on the page
            connectors = [shape for shape in page.Shapes 
                         if shape.Master and shape.Master.NameU == "Dynamic connector"]
            
            # Build a graph of connector paths
            paths = []
            for conn in connectors:
                begin = (conn.Cells("BeginX").Result(""), 
                        conn.Cells("BeginY").Result(""))
                end = (conn.Cells("EndX").Result(""), 
                      conn.Cells("EndY").Result(""))
                paths.append((begin, end))
            
            # Find intersections between connectors
            intersections = self._find_connector_intersections(paths)
            
            # Adjust connector paths to minimize crossings
            if intersections:
                # Add intermediate points to route around intersections
                for point in self._calculate_routing_points(intersections):
                    connector.AddSection(1)  # Add segment
                    connector.Cells("Geometry1.X1").FormulaU = f"{point[0]} in"
                    connector.Cells("Geometry1.Y1").FormulaU = f"{point[1]} in"
            
            connector.AutoRoute()
        except Exception as e:
            logger.warning(f"Failed to apply network flow routing: {str(e)}")
            connector.AutoRoute()  # Fallback to auto-routing
    
    def _find_connector_intersections(
        self, paths: List[Tuple[Tuple[float, float], Tuple[float, float]]]
    ) -> List[Tuple[float, float]]:
        """Find intersection points between connector paths"""
        intersections = []
        for i, path1 in enumerate(paths):
            for path2 in paths[i+1:]:
                if intersection := self._line_intersection(path1[0], path1[1], 
                                                         path2[0], path2[1]):
                    intersections.append(intersection)
        return intersections
    
    def _line_intersection(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        p4: Tuple[float, float]
    ) -> Optional[Tuple[float, float]]:
        """Calculate intersection point of two line segments"""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        denominator = ((x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4))
        if denominator == 0:
            return None
        
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator
        
        if 0 <= t <= 1 and 0 <= u <= 1:
            x = x1 + t * (x2 - x1)
            y = y1 + t * (y2 - y1)
            return (x, y)
        
        return None
    
    def _calculate_routing_points(
        self, intersections: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """Calculate routing points to avoid intersections"""
        points = []
        for x, y in intersections:
            # Add offset points around intersection
            offset = 0.25  # 0.25 inches
            points.extend([
                (x - offset, y - offset),
                (x + offset, y + offset)
            ])
        return points

    async def _get_template(self, template_name: str) -> Path:
        """Get template path from cache or template directory"""
        template_path = self.template_dir / template_name
        
        # Check cache first
        if cached_path := await self.cache_service.get_cached_file(template_path):
            return cached_path
        
        # If not in cache, verify template exists
        if not template_path.exists():
            raise VisioError(f"Template not found: {template_name}")
        
        # Cache template for future use
        cached_path = await self.cache_service.cache_file(template_path)
        if not cached_path:
            raise VisioError(f"Failed to cache template: {template_name}")
        
        return cached_path

    async def _generate_dynamic_text(
        self,
        config: DynamicText,
        ai_service: AIServiceManager
    ) -> str:
        """Generate dynamic text using AI service"""
        try:
            response = await ai_service.generate_text(
                prompt=config.prompt_template,
                context=config.context,
                max_tokens=config.max_length,
                style=config.style
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating dynamic text: {str(e)}")
            raise

    def _add_dynamic_content(
        self,
        shape: any,
        content: DynamicContent
    ) -> None:
        """Add dynamic content to a shape"""
        try:
            if content.hyperlink:
                shape.Hyperlink = content.hyperlink
            
            if content.tooltip:
                shape.CellsSRC(1, 999, 0).FormulaU = f"\"{content.tooltip}\""
            
            if content.hover_text:
                shape.CellsSRC(1, 998, 0).FormulaU = f"\"{content.hover_text}\""
            
            if content.custom_properties:
                for prop_name, prop_value in content.custom_properties.items():
                    try:
                        prop = shape.AddRow(
                            1,  # visSectionProp
                            -1,  # visRowLast
                            0   # visTagDefault
                        )
                        prop.NameU = prop_name
                        prop.Value = str(prop_value)
                    except Exception as e:
                        logger.warning(f"Failed to add custom property {prop_name}: {str(e)}")
        
        except Exception as e:
            logger.warning(f"Failed to add dynamic content: {str(e)}")

    def _add_header_footer(
        self,
        page: any,
        text: str,
        is_header: bool = True
    ) -> None:
        """Add header or footer to a page"""
        try:
            y = page.PageSheet.CellsSRC(1, 3, 0).Result("") # Get page height
            shape = page.DrawRectangle(
                0.5,  # Left margin
                y - 0.5 if is_header else 0.5,  # Top/bottom position
                page.PageSheet.CellsSRC(1, 2, 0).Result("") - 0.5,  # Right margin
                y - 1.0 if is_header else 1.0  # Bottom/top position
            )
            shape.Text = text
            shape.Cells("LinePattern").FormulaU = "0"  # No border
            shape.Cells("FillPattern").FormulaU = "0"  # No fill
            shape.Cells("HAlign").FormulaU = "2"  # Center align
            
        except Exception as e:
            logger.warning(f"Failed to add {'header' if is_header else 'footer'}: {str(e)}") 

    def _add_spec_content(self, diagram, specs):
        """Embed specs into Visio shapes"""
        for shape in diagram.shapes:
            if spec := specs.get(shape.name):
                self._add_spec_callout(shape, spec)
                self._add_3d_dimensions(shape, spec)
                self._add_compatibility_warnings(shape, spec)

    def _add_spec_callout(self, shape, spec):
        """Add spec data to shape metadata"""
        shape.properties.update({
            "specs": {
                "dimensions": spec.get("dimensions"),
                "power": spec.get("power_requirements"),
                "ports": spec.get("port_configuration")
            }
        })

    def apply_ai_optimized_routing(self):
        adviser = AILayoutAdviser()
        suggestions = adviser.analyze_diagram(self.export_json())
        
        # Apply AI suggestions
        self._group_components(suggestions.component_groups)
        self._optimize_spacing(suggestions.spacing_recommendations)
        
        # Enhanced routing with AI insights
        router = HybridRouter(
            ai_suggestions=suggestions.optimal_routes,
            config=self.routing_config
        )
        router.optimize_all_paths()

    def _group_components(self, component_groups):
        # Implementation of _group_components method
        pass

    def _optimize_spacing(self, spacing_recommendations):
        # Implementation of _optimize_spacing method
        pass

    def _export_json(self):
        # Implementation of _export_json method
        pass

    async def _apply_ai_routing(self, page, shape_map):
        """Apply AI-enhanced routing to page"""
        router = HybridRouter(
            visio_page=page,
            config=self.routing_config,
            constraints=self.routing_constraints
        )
        
        for connector in page.connectors:
            router.add_connector(connector)
            
        for shape in shape_map.values():
            router.add_obstacle(shape)
            
        await router.optimize_all_paths()

class VisioGenerator:
    def __init__(self):
        self.spec_service = TechSpecsService()
        self.context_enricher = ScreenPipeAdapter()
        self.spec_search = SpecSearch()
        self.style_guide = VisioStyleGuideService()
        
    async def generate_diagram(self, requirements):
        # Get real-time design context
        context = await self._capture_design_context()
        
        # Retrieve and validate specs
        specs = await self._get_validated_specs(context)
        
        # Generate Visio with embedded specs
        diagram = self._create_base_diagram(requirements)
        self._add_spec_content(diagram, specs)
        
        return self._finalize_diagram(diagram)

    async def _capture_design_context(self):
        """Capture multi-source design context"""
        return {
            "visual": self.context_enricher.get_design_context(),
            "spec_history": self.spec_service.get_recent_specs(),
            "active_components": await self._detect_components()
        }

    async def _get_validated_specs(self, context):
        # Implementation of _get_validated_specs method
        pass

    def _create_base_diagram(self, requirements):
        # Implementation of _create_base_diagram method
        pass

    def _add_spec_content(self, diagram, specs):
        # Implementation of _add_spec_content method
        pass

    def _finalize_diagram(self, diagram):
        # Implementation of _finalize_diagram method
        pass

    async def _detect_components(self):
        # Implementation of _detect_components method
        pass

    def _add_spec_content(self, diagram, specs):
        # Implementation of _add_spec_content method
        pass

    def _finalize_diagram(self, diagram):
        # Implementation of _finalize_diagram method
        pass

    async def _detect_components(self):
        # Implementation of _detect_components method
        pass 