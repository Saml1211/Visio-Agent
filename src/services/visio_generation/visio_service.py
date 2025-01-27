from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import win32com.client
import logging
import json
from pathlib import Path
import pythoncom
from PIL import Image
import tempfile
import os

from ..ai_service_config import AIServiceManager
from ..rag_memory_service import RAGMemoryService

logger = logging.getLogger(__name__)

class ConnectorType(str, Enum):
    """Types of connectors supported"""
    STRAIGHT = "straight"
    CURVED = "curved"
    ORTHOGONAL = "orthogonal"

class ShapeType(str, Enum):
    """Types of shapes supported"""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    DIAMOND = "diamond"
    CUSTOM = "custom"

@dataclass
class ShapeStyle:
    """Style configuration for shapes"""
    fill_color: Optional[str] = None
    line_color: Optional[str] = None
    line_weight: Optional[float] = None
    line_pattern: Optional[str] = None
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    font_color: Optional[str] = None
    opacity: Optional[float] = None
    custom_properties: Optional[Dict[str, Any]] = None

@dataclass
class ShapeConfig:
    """Configuration for a shape in the diagram"""
    shape_type: ShapeType
    position: Tuple[float, float]
    size: Tuple[float, float]
    text: Optional[str] = None
    stencil_name: Optional[str] = None
    master_name: Optional[str] = None
    style: Optional[ShapeStyle] = None
    data: Optional[Dict[str, Any]] = None
    layer: Optional[str] = None
    id: Optional[str] = None

@dataclass
class ConnectorConfig:
    """Configuration for a connector in the diagram"""
    from_shape_id: str
    to_shape_id: str
    connector_type: ConnectorType
    label: Optional[str] = None
    style: Optional[ShapeStyle] = None
    routing_points: Optional[List[Tuple[float, float]]] = None

@dataclass
class PageConfig:
    """Configuration for a page in the diagram"""
    name: str
    shapes: List[ShapeConfig]
    connectors: List[ConnectorConfig]
    size: Optional[Tuple[float, float]] = None
    orientation: Optional[str] = None
    background: Optional[str] = None
    header: Optional[str] = None
    footer: Optional[str] = None
    page_number: Optional[int] = None  # For explicit page ordering
    theme: Optional[str] = None  # For consistent page styling
    scale: Optional[float] = 1.0  # Page scaling factor
    grid_visible: Optional[bool] = True  # Show/hide grid
    guides_visible: Optional[bool] = True  # Show/hide guides
    margin: Optional[Tuple[float, float, float, float]] = None  # Left, Top, Right, Bottom margins in inches

class VisioGenerationService:
    """Enhanced service for generating Visio diagrams"""
    
    def __init__(
        self,
        ai_service_manager: AIServiceManager,
        rag_memory: RAGMemoryService,
        templates_dir: Optional[Path] = None,
        stencils_dir: Optional[Path] = None
    ):
        """Initialize the Visio generation service
        
        Args:
            ai_service_manager: Manager for AI services
            rag_memory: RAG memory service for context
            templates_dir: Directory containing Visio templates
            stencils_dir: Directory containing custom stencils
        """
        self.ai_service_manager = ai_service_manager
        self.rag_memory = rag_memory
        self.templates_dir = templates_dir or Path("config/templates")
        self.stencils_dir = stencils_dir or Path("config/stencils")
        
        # Create directories if they don't exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.stencils_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize COM in the current thread
        pythoncom.CoInitialize()
        
        # Create Visio application instance
        self.visio = win32com.client.Dispatch("Visio.Application")
        self.visio.Visible = False  # Run in background
        
        logger.info("Initialized Visio generation service")
    
    async def generate_diagram(
        self,
        template_name: str,
        pages: List[PageConfig],
        output_dir: Path,
        filename: str,
        validate_with_ai: bool = True
    ) -> Tuple[Path, Path]:
        """Generate a Visio diagram with multiple pages
        
        Args:
            template_name: Name of the template to use
            pages: List of page configurations
            output_dir: Directory to save output files
            filename: Base name for output files
            validate_with_ai: Whether to use AI for validation
            
        Returns:
            Tuple of paths to the generated VSDX and PDF files
        """
        try:
            # Load template
            template_path = self.templates_dir / f"{template_name}.vstx"
            if not template_path.exists():
                raise ValueError(f"Template not found: {template_name}")
            
            # Create new document from template
            doc = self.visio.Documents.Add(str(template_path))
            
            # Sort pages by page_number if specified
            sorted_pages = sorted(pages, key=lambda p: (p.page_number if p.page_number is not None else float('inf')))
            
            # Process each page
            for page_config in sorted_pages:
                # Create or get page
                if page_config.name in [p.Name for p in doc.Pages]:
                    page = doc.Pages.Item(page_config.name)
                else:
                    page = doc.Pages.Add()
                    page.Name = page_config.name
                
                # Set page properties
                if page_config.size:
                    page.PageSheet.CellsSRC(
                        1, 2, 0  # visSectionObject, visRowPage, visPageWidth
                    ).FormulaU = f"{page_config.size[0]} in"
                    page.PageSheet.CellsSRC(
                        1, 2, 1  # visSectionObject, visRowPage, visPageHeight
                    ).FormulaU = f"{page_config.size[1]} in"
                
                if page_config.orientation:
                    page.PageSheet.CellsSRC(
                        1, 2, 2  # visSectionObject, visRowPage, visPageOrientation
                    ).FormulaU = "1" if page_config.orientation.lower() == "landscape" else "0"
                
                # Set page scale
                if page_config.scale != 1.0:
                    page.PageSheet.CellsSRC(
                        1, 2, 5  # visSectionObject, visRowPage, visPageScale
                    ).FormulaU = str(page_config.scale)
                
                # Set page margins
                if page_config.margin:
                    left, top, right, bottom = page_config.margin
                    page.PageSheet.CellsSRC(
                        1, 2, 3  # visSectionObject, visRowPage, visPageMarginLeft
                    ).FormulaU = f"{left} in"
                    page.PageSheet.CellsSRC(
                        1, 2, 4  # visSectionObject, visRowPage, visPageMarginTop
                    ).FormulaU = f"{top} in"
                    page.PageSheet.CellsSRC(
                        1, 2, 5  # visSectionObject, visRowPage, visPageMarginRight
                    ).FormulaU = f"{right} in"
                    page.PageSheet.CellsSRC(
                        1, 2, 6  # visSectionObject, visRowPage, visPageMarginBottom
                    ).FormulaU = f"{bottom} in"
                
                # Set grid and guides visibility
                page.PageSheet.CellsSRC(
                    1, 2, 7  # visSectionObject, visRowPage, visPageGridVisible
                ).FormulaU = "1" if page_config.grid_visible else "0"
                page.PageSheet.CellsSRC(
                    1, 2, 8  # visSectionObject, visRowPage, visPageGuidesVisible
                ).FormulaU = "1" if page_config.guides_visible else "0"
                
                # Apply theme if specified
                if page_config.theme:
                    theme_path = self.templates_dir / "themes" / f"{page_config.theme}.vst"
                    if theme_path.exists():
                        page.ApplyTheme(str(theme_path))
                    else:
                        logger.warning(f"Theme not found: {page_config.theme}")
                
                # Add shapes
                shape_map = {}  # Map shape IDs to Visio shape objects
                for shape_config in page_config.shapes:
                    shape = await self._add_shape(page, shape_config)
                    if shape_config.id:
                        shape_map[shape_config.id] = shape
                
                # Add connectors
                for connector_config in page_config.connectors:
                    await self._add_connector(
                        page,
                        connector_config,
                        shape_map
                    )
                
                # Set header/footer
                if page_config.header:
                    page.HeaderFooter.HeaderCenter = page_config.header
                if page_config.footer:
                    page.HeaderFooter.FooterCenter = page_config.footer
            
            # Save paths
            output_dir.mkdir(parents=True, exist_ok=True)
            vsdx_path = output_dir / f"{filename}.vsdx"
            pdf_path = output_dir / f"{filename}.pdf"
            
            # Save as VSDX
            doc.SaveAs(str(vsdx_path))
            
            # Export as PDF with all pages
            doc.ExportAsFixedFormat(
                1,  # PDF format
                str(pdf_path),
                0,  # Intent: Standard
                1,  # Print quality: High
                1,  # From: Page 1
                doc.Pages.Count  # To: Last page
            )
            
            # Validate with AI if requested
            if validate_with_ai:
                await self._validate_diagram_with_ai(
                    vsdx_path,
                    pdf_path,
                    sorted_pages
                )
            
            logger.info(
                f"Generated diagram: {vsdx_path} "
                f"with {len(pages)} pages"
            )
            
            return vsdx_path, pdf_path
            
        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}")
            raise
        
        finally:
            # Cleanup
            if 'doc' in locals():
                doc.Close()
    
    async def _add_shape(
        self,
        page: Any,
        config: ShapeConfig
    ) -> Any:
        """Add a shape to the page
        
        Args:
            page: Visio page object
            config: Shape configuration
            
        Returns:
            Visio shape object
        """
        try:
            shape = None
            
            if config.shape_type == ShapeType.CUSTOM:
                # Load custom stencil
                if not config.stencil_name or not config.master_name:
                    raise ValueError("Stencil and master names required for custom shapes")
                
                stencil_path = self.stencils_dir / f"{config.stencil_name}.vssx"
                if not stencil_path.exists():
                    raise ValueError(f"Stencil not found: {config.stencil_name}")
                
                stencil = self.visio.Documents.OpenEx(
                    str(stencil_path),
                    64  # visOpenStencil
                )
                
                # Drop custom shape
                master = stencil.Masters.Item(config.master_name)
                shape = page.Drop(
                    master,
                    config.position[0],
                    config.position[1]
                )
                
                stencil.Close()
                
            else:
                # Drop basic shape
                shape = page.DrawRectangle(
                    config.position[0],
                    config.position[1],
                    config.position[0] + config.size[0],
                    config.position[1] + config.size[1]
                )
                
                # Set shape type
                if config.shape_type == ShapeType.CIRCLE:
                    shape.SetFormula("Width", "Height")
                    shape.SetFormula("Geometry1.NoFill", "0")
                    shape.SetFormula("Geometry1.NoLine", "0")
                elif config.shape_type == ShapeType.DIAMOND:
                    shape.SetFormula("Geometry1.NoFill", "0")
                    shape.SetFormula("Geometry1.NoLine", "0")
                    shape.SetFormula("Geometry1.X1", "Width*0")
                    shape.SetFormula("Geometry1.Y1", "Height*0.5")
                    shape.SetFormula("Geometry1.X2", "Width*0.5")
                    shape.SetFormula("Geometry1.Y2", "Height*0")
                    shape.SetFormula("Geometry1.X3", "Width*1")
                    shape.SetFormula("Geometry1.Y3", "Height*0.5")
                    shape.SetFormula("Geometry1.X4", "Width*0.5")
                    shape.SetFormula("Geometry1.Y4", "Height*1")
            
            # Set text
            if config.text:
                shape.Text = config.text
            
            # Apply style
            if config.style:
                await self._apply_style(shape, config.style)
            
            # Set shape data
            if config.data:
                for key, value in config.data.items():
                    shape.AddSection(1)  # visSectionProp
                    row = shape.AddRow(
                        1,  # visSectionProp
                        -1,  # visRowLast
                        0   # visTagDefault
                    )
                    shape.CellsSRC(
                        1,  # visSectionProp
                        row,
                        0   # visCustPropsLabel
                    ).FormulaU = f'"{key}"'
                    shape.CellsSRC(
                        1,  # visSectionProp
                        row,
                        1   # visCustPropsValue
                    ).FormulaU = f'"{value}"'
            
            # Set layer
            if config.layer:
                layer = None
                for l in page.Layers:
                    if l.Name == config.layer:
                        layer = l
                        break
                
                if not layer:
                    layer = page.Layers.Add(config.layer)
                
                shape.Layer = layer.Index
            
            return shape
            
        except Exception as e:
            logger.error(f"Error adding shape: {str(e)}")
            raise
    
    async def _add_connector(
        self,
        page: Any,
        config: ConnectorConfig,
        shape_map: Dict[str, Any]
    ) -> Any:
        """Add a connector between shapes
        
        Args:
            page: Visio page object
            config: Connector configuration
            shape_map: Map of shape IDs to Visio shape objects
            
        Returns:
            Visio connector object
        """
        try:
            # Get shapes
            from_shape = shape_map.get(config.from_shape_id)
            to_shape = shape_map.get(config.to_shape_id)
            
            if not from_shape or not to_shape:
                raise ValueError("Invalid shape IDs for connector")
            
            # Create connector
            connector = page.Drop(
                page.Application.ConnectorToolDataObject,
                0,
                0
            )
            
            # Connect shapes
            connector.CellsU("BeginX").GlueTo(from_shape.CellsU("PinX"))
            connector.CellsU("EndX").GlueTo(to_shape.CellsU("PinX"))
            
            # Set connector type
            if config.connector_type == ConnectorType.CURVED:
                connector.CellsU("Rounding").Formula = "0.5"
            elif config.connector_type == ConnectorType.ORTHOGONAL:
                connector.AutoRoute = True
            
            # Add routing points
            if config.routing_points:
                for i, point in enumerate(config.routing_points, 1):
                    connector.AddSection(2)  # visSectionFirstVertex
                    row = connector.AddRow(
                        2,  # visSectionFirstVertex
                        -1,  # visRowLast
                        0   # visTagDefault
                    )
                    connector.CellsSRC(
                        2,  # visSectionFirstVertex
                        row,
                        0   # visVertexX
                    ).FormulaU = f"{point[0]}"
                    connector.CellsSRC(
                        2,  # visSectionFirstVertex
                        row,
                        1   # visVertexY
                    ).FormulaU = f"{point[1]}"
            
            # Set label
            if config.label:
                connector.Text = config.label
            
            # Apply style
            if config.style:
                await self._apply_style(connector, config.style)
            
            return connector
            
        except Exception as e:
            logger.error(f"Error adding connector: {str(e)}")
            raise
    
    async def _apply_style(
        self,
        shape: Any,
        style: ShapeStyle
    ) -> None:
        """Apply style to a shape or connector
        
        Args:
            shape: Visio shape object
            style: Style configuration
        """
        try:
            if style.fill_color:
                shape.CellsU("FillForegnd").FormulaU = f'"{style.fill_color}"'
            
            if style.line_color:
                shape.CellsU("LineColor").FormulaU = f'"{style.line_color}"'
            
            if style.line_weight:
                shape.CellsU("LineWeight").FormulaU = f"{style.line_weight} pt"
            
            if style.line_pattern:
                shape.CellsU("LinePattern").FormulaU = style.line_pattern
            
            if style.font_name:
                shape.CellsU("Char.Font").FormulaU = f'"{style.font_name}"'
            
            if style.font_size:
                shape.CellsU("Char.Size").FormulaU = f"{style.font_size} pt"
            
            if style.font_color:
                shape.CellsU("Char.Color").FormulaU = f'"{style.font_color}"'
            
            if style.opacity is not None:
                shape.CellsU("FillForegndTrans").FormulaU = f"{(1 - style.opacity) * 100}%"
            
            if style.custom_properties:
                for key, value in style.custom_properties.items():
                    shape.CellsU(key).FormulaU = f'"{value}"'
            
        except Exception as e:
            logger.error(f"Error applying style: {str(e)}")
            raise
    
    async def _validate_diagram_with_ai(
        self,
        vsdx_path: Path,
        pdf_path: Path,
        pages: List[PageConfig]
    ) -> None:
        """Validate diagram using AI service
        
        Args:
            vsdx_path: Path to VSDX file
            pdf_path: Path to PDF file
            pages: Original page configurations
        """
        try:
            # Get AI service
            ai_provider = self.ai_service_manager.get_provider()
            
            # Convert PDF to images for analysis
            with tempfile.TemporaryDirectory() as temp_dir:
                images = []
                pdf_images = Image.open(pdf_path)
                for i in range(pdf_images.n_frames):
                    pdf_images.seek(i)
                    image_path = Path(temp_dir) / f"page_{i}.png"
                    pdf_images.save(image_path)
                    images.append(image_path)
                
                # Analyze each page
                for i, (image_path, page_config) in enumerate(zip(images, pages)):
                    # Generate validation prompt
                    prompt = f"""
                    Analyze this diagram page and validate:
                    1. Layout and spacing
                    2. Connector routing
                    3. Text readability
                    4. Color contrast
                    5. Consistency with requirements
                    
                    Page name: {page_config.name}
                    Number of shapes: {len(page_config.shapes)}
                    Number of connectors: {len(page_config.connectors)}
                    
                    Provide specific issues and suggestions for improvement.
                    """
                    
                    # Get AI analysis
                    with open(image_path, "rb") as f:
                        analysis = await ai_provider.analyze_image(
                            image_data=f.read(),
                            prompt=prompt
                        )
                    
                    logger.info(
                        f"AI validation for page {page_config.name}:\n{analysis}"
                    )
            
        except Exception as e:
            logger.error(f"Error validating diagram with AI: {str(e)}")
            # Don't raise - validation errors shouldn't block generation
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.visio:
                self.visio.Quit()
                pythoncom.CoUninitialize()
        except Exception as e:
            logger.error(f"Error cleaning up Visio resources: {str(e)}")
            raise 