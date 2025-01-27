import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile
import win32com.client
import pythoncom
from PIL import Image
import io

from src.services.visio_generation_service import (
    VisioGenerationService,
    VisioDocument,
    VisioShape,
    ShapeConfig,
    ConnectorConfig,
    Point,
    ConnectorStyle,
    ConnectorRouting,
    InternalShape,
    InternalShapeType,
    ConnectionPoint,
    CustomConnectionPoint,
    ShapeStyle,
    PageConfig,
    DynamicContent,
    DynamicText,
    CustomValidationRule,
    ValidationSeverity,
    ShapeType,
    ConnectorType,
    VisioGenerationError
)
from src.services.ai_service_config import AIServiceManager, AIServiceProvider
from src.services.file_cache_service import FileCacheService
from src.services.exceptions import VisioError
from src.services.rag_memory_service import RAGMemoryService

@pytest.fixture
def mock_win32com():
    with patch('win32com.client.Dispatch') as mock:
        # Mock Visio application
        visio_app = MagicMock()
        
        # Mock document
        doc = MagicMock()
        visio_app.Documents.Add.return_value = doc
        
        # Mock page
        page = MagicMock()
        doc.Pages.Item.return_value = page
        
        # Mock shape operations
        master = MagicMock()
        doc.Masters.ItemU.__getitem__.return_value = master
        
        shape = MagicMock()
        page.Drop.return_value = shape
        
        # Return mock application
        mock.return_value = visio_app
        yield mock

@pytest.fixture
def mock_pythoncom():
    with patch('pythoncom.CoInitialize') as init_mock, \
         patch('pythoncom.CoUninitialize') as uninit_mock:
        yield init_mock, uninit_mock

@pytest.fixture
def mock_ai_provider():
    provider = MagicMock()
    provider.analyze_image = AsyncMock(return_value="Test analysis")
    return provider

@pytest.fixture
def mock_ai_service_manager(mock_ai_provider):
    manager = MagicMock(spec=AIServiceManager)
    manager.get_provider.return_value = mock_ai_provider
    return manager

@pytest.fixture
def mock_rag_memory():
    return MagicMock(spec=RAGMemoryService)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def cache_service(temp_dir):
    return FileCacheService(
        cache_dir=temp_dir / "cache",
        max_cache_size=5 * 1024 * 1024,  # 5MB
        cache_ttl=60,  # 1 minute
        cleanup_interval=5  # 5 seconds
    )

@pytest.fixture
def visio_service(
    mock_ai_service_manager,
    mock_rag_memory,
    test_template,
    test_stencil,
    mock_visio
):
    with patch("win32com.client.Dispatch", return_value=mock_visio):
        with patch("pythoncom.CoInitialize"):
            service = VisioGenerationService(
                ai_service_manager=mock_ai_service_manager,
                rag_memory=mock_rag_memory,
                templates_dir=test_template,
                stencils_dir=test_stencil
            )
            yield service
            service.cleanup()

@pytest.fixture
def mock_visio():
    """Mock Visio application and related objects"""
    mock_app = MagicMock()
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_shape = MagicMock()
    mock_fonts = MagicMock()
    
    # Set up font mocking
    mock_font = MagicMock()
    mock_font.Name = "Arial"
    mock_fonts.__iter__.return_value = [mock_font]
    mock_app.Fonts = mock_fonts
    
    # Set up shape mocking
    mock_page.Drop.return_value = mock_shape
    mock_doc.Pages.Add.return_value = mock_page
    mock_app.Documents.Add.return_value = mock_doc
    
    return mock_app, mock_doc, mock_page, mock_shape

@pytest.fixture
def mock_shape():
    """Mock a Visio shape with cells"""
    shape = MagicMock()
    cells = {}
    
    def get_cell(name):
        if name not in cells:
            cell = MagicMock()
            cell.Exists = True
            cells[name] = cell
        return cells[name]
    
    shape.Cells = MagicMock(side_effect=get_cell)
    shape.CellsSRC = MagicMock(return_value=MagicMock(Exists=True))
    return shape

def test_service_initialization(tmp_path, mock_ai_service_manager):
    # Test paths
    templates_dir = tmp_path / "templates"
    output_dir = tmp_path / "output"
    stencils_dir = tmp_path / "stencils"
    
    # Initialize service
    service = VisioGenerationService(
        templates_dir=templates_dir,
        output_dir=output_dir,
        stencils_dir=stencils_dir,
        ai_service_manager=mock_ai_service_manager
    )
    
    # Check directories were created
    assert templates_dir.exists()
    assert output_dir.exists()
    assert stencils_dir.exists()
    assert service.ai_service_manager == mock_ai_service_manager

def test_optimize_layout(visio_service, mock_ai_provider):
    # Test data
    shapes = [
        VisioShape(
            shape_type="Rectangle",
            name="Shape1",
            x=0.0,
            y=0.0
        ),
        VisioShape(
            shape_type="Circle",
            name="Shape2",
            x=0.0,
            y=0.0
        )
    ]
    
    # Optimize layout
    optimized_shapes = visio_service.optimize_layout(shapes)
    
    # Verify AI service was called
    mock_ai_provider.analyze_image.assert_called_once()
    
    # Verify shapes were updated
    assert optimized_shapes[0].x == 1.0
    assert optimized_shapes[0].y == 1.0
    assert optimized_shapes[1].x == 3.0
    assert optimized_shapes[1].y == 1.0

def test_optimize_layout_no_ai_service(tmp_path):
    # Initialize service without AI
    service = VisioGenerationService(
        templates_dir=tmp_path / "templates",
        output_dir=tmp_path / "output"
    )
    
    # Test data
    shapes = [
        VisioShape(
            shape_type="Rectangle",
            name="Shape1",
            x=1.0,
            y=1.0
        )
    ]
    
    # Optimize layout
    optimized_shapes = service.optimize_layout(shapes)
    
    # Verify shapes unchanged
    assert optimized_shapes[0].x == 1.0
    assert optimized_shapes[0].y == 1.0

def test_optimize_layout_error_handling(visio_service, mock_ai_provider):
    # Configure AI to raise error
    mock_ai_provider.analyze_image.side_effect = Exception("AI error")
    
    # Test data
    shapes = [
        VisioShape(
            shape_type="Rectangle",
            name="Shape1",
            x=1.0,
            y=1.0
        )
    ]
    
    # Optimize layout
    optimized_shapes = visio_service.optimize_layout(shapes)
    
    # Verify shapes unchanged on error
    assert optimized_shapes[0].x == 1.0
    assert optimized_shapes[0].y == 1.0

def test_generate_diagram_with_layout_optimization(visio_service, mock_win32com, mock_pythoncom, mock_ai_provider):
    # Test data
    document = VisioDocument(
        template_path="test.vstx",
        shapes=[
            VisioShape(
                shape_type="Rectangle",
                name="Shape1",
                x=0.0,
                y=0.0,
                connections=[
                    {
                        "target": "Shape2",
                        "properties": {"LinePattern": "2"}
                    }
                ]
            ),
            VisioShape(
                shape_type="Rectangle",
                name="Shape2",
                x=0.0,
                y=0.0
            )
        ]
    )
    
    # Generate diagram
    visio_path, pdf_path = visio_service.generate_diagram(
        document=document,
        output_filename="test_diagram",
        optimize_layout=True
    )
    
    # Verify AI service was called
    mock_ai_provider.analyze_image.assert_called_once()
    
    # Verify COM operations
    mock_win32com.assert_called_once()
    mock_pythoncom[0].assert_called_once()
    mock_pythoncom[1].assert_called_once()

def test_generate_diagram_without_layout_optimization(visio_service, mock_win32com, mock_pythoncom, mock_ai_provider):
    # Test data
    document = VisioDocument(
        template_path="test.vstx",
        shapes=[
            VisioShape(
                shape_type="Rectangle",
                name="Shape1",
                x=1.0,
                y=1.0
            )
        ]
    )
    
    # Generate diagram
    visio_path, pdf_path = visio_service.generate_diagram(
        document=document,
        output_filename="test_diagram",
        optimize_layout=False
    )
    
    # Verify AI service was not called
    mock_ai_provider.analyze_image.assert_not_called()
    
    # Verify COM operations
    mock_win32com.assert_called_once()
    mock_pythoncom[0].assert_called_once()
    mock_pythoncom[1].assert_called_once()

def test_create_layout_prompt(visio_service):
    # Test data
    shapes = [
        VisioShape(
            shape_type="Rectangle",
            name="Shape1",
            x=1.0,
            y=1.0,
            connections=[{"target": "Shape2"}]
        ),
        VisioShape(
            shape_type="Circle",
            name="Shape2",
            x=2.0,
            y=2.0
        )
    ]
    
    # Create prompt
    prompt = visio_service._create_layout_prompt(shapes)
    
    # Verify prompt content
    assert "Shape1 (Rectangle) connected to: Shape2" in prompt
    assert "Shape2 (Circle)" in prompt
    assert "optimal x,y coordinates" in prompt

def test_apply_layout_suggestions(visio_service):
    # Test data
    shapes = [
        VisioShape(
            shape_type="Rectangle",
            name="Shape1",
            x=0.0,
            y=0.0
        ),
        VisioShape(
            shape_type="Circle",
            name="Shape2",
            x=0.0,
            y=0.0
        )
    ]
    
    ai_response = """
    Shape1: 1.5, 2.5
    Shape2: 3.5, 4.5
    Invalid: not,coords
    """
    
    # Apply suggestions
    updated_shapes = visio_service._apply_layout_suggestions(shapes, ai_response)
    
    # Verify coordinates were updated
    assert updated_shapes[0].x == 1.5
    assert updated_shapes[0].y == 2.5
    assert updated_shapes[1].x == 3.5
    assert updated_shapes[1].y == 4.5

def test_generate_diagram(visio_service, mock_win32com, mock_pythoncom):
    # Test data
    document = VisioDocument(
        template_path="test.vstx",
        shapes=[
            VisioShape(
                shape_type="Rectangle",
                name="Shape1",
                x=1.0,
                y=1.0,
                text="Test Shape"
            )
        ]
    )
    
    # Generate diagram
    visio_path, pdf_path = visio_service.generate_diagram(
        document=document,
        output_filename="test_diagram"
    )
    
    # Check paths
    assert visio_path == visio_service.output_dir / "test_diagram.vsdx"
    assert pdf_path == visio_service.output_dir / "test_diagram.pdf"
    
    # Verify COM operations
    mock_win32com.assert_called_once_with("Visio.Application")
    mock_pythoncom[0].assert_called_once()  # CoInitialize
    mock_pythoncom[1].assert_called_once()  # CoUninitialize

def test_add_shape(visio_service, mock_win32com):
    # Test data
    shape = VisioShape(
        shape_type="Rectangle",
        name="TestShape",
        x=1.0,
        y=1.0,
        width=2.0,
        height=1.5,
        text="Test Shape",
        properties={"LineWeight": "2 pt"}
    )
    
    # Mock document and page
    doc = MagicMock()
    page = MagicMock()
    
    # Add shape
    visio_shape = visio_service._add_shape(doc, page, shape)
    
    # Verify shape operations
    assert visio_shape is not None
    page.Drop.assert_called_once()
    visio_shape.Text = shape.text
    visio_shape.Cells.assert_any_call("Width")
    visio_shape.Cells.assert_any_call("Height")

def test_add_connections(visio_service, mock_win32com):
    # Test data
    shape_map = {
        "Shape1": MagicMock(),
        "Shape2": MagicMock()
    }
    
    connections = [
        {
            "target": "Shape2",
            "properties": {"LinePattern": "2"}
        }
    ]
    
    # Mock page
    page = MagicMock()
    connector = MagicMock()
    page.Drop.return_value = connector
    
    # Add connections
    visio_service._add_connections(
        page=page,
        shape_map=shape_map,
        source_name="Shape1",
        connections=connections
    )
    
    # Verify connector operations
    page.Drop.assert_called_once()
    connector.CellsU.__getitem__.assert_any_call("BeginX")
    connector.CellsU.__getitem__.assert_any_call("EndX")

def test_generate_diagram_with_connections(visio_service, mock_win32com, mock_pythoncom):
    # Test data
    document = VisioDocument(
        template_path="test.vstx",
        shapes=[
            VisioShape(
                shape_type="Rectangle",
                name="Shape1",
                x=1.0,
                y=1.0,
                connections=[
                    {
                        "target": "Shape2",
                        "properties": {"LinePattern": "2"}
                    }
                ]
            ),
            VisioShape(
                shape_type="Rectangle",
                name="Shape2",
                x=3.0,
                y=1.0
            )
        ]
    )
    
    # Generate diagram
    visio_path, pdf_path = visio_service.generate_diagram(
        document=document,
        output_filename="test_diagram"
    )
    
    # Verify COM operations
    mock_win32com.assert_called_once()
    mock_pythoncom[0].assert_called_once()
    mock_pythoncom[1].assert_called_once()

def test_generate_diagram_error_handling(visio_service, mock_win32com):
    # Mock error in Visio operations
    mock_win32com.side_effect = Exception("Visio error")
    
    # Test data
    document = VisioDocument(
        template_path="test.vstx",
        shapes=[]
    )
    
    # Test error handling
    with pytest.raises(Exception) as exc_info:
        visio_service.generate_diagram(
            document=document,
            output_filename="test_diagram"
        )
    
    assert "Visio error" in str(exc_info.value)

def test_add_shape_with_custom_stencil(visio_service, mock_win32com):
    # Create test stencil
    stencil_path = visio_service.stencils_dir / "CustomShape.vssx"
    stencil_path.touch()
    
    # Test data
    shape = VisioShape(
        shape_type="CustomShape",
        name="TestShape",
        x=1.0,
        y=1.0
    )
    
    # Mock document and page
    doc = MagicMock()
    page = MagicMock()
    
    # Mock stencil operations
    stencil = MagicMock()
    doc.Application.Documents.OpenEx.return_value = stencil
    master = MagicMock()
    stencil.Masters.ItemU.__getitem__.return_value = master
    
    # Add shape
    visio_shape = visio_service._add_shape(doc, page, shape)
    
    # Verify stencil operations
    assert visio_shape is not None
    doc.Application.Documents.OpenEx.assert_called_once_with(
        str(stencil_path),
        64  # visOpenStencil
    )

def create_test_template(path: Path) -> None:
    """Create a test Visio template"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()

@pytest.mark.asyncio
async def test_generate_diagram_success(visio_service, temp_dir, mock_visio):
    # Create test template
    template_name = "test.vstx"
    template_path = visio_service.template_dir / template_name
    create_test_template(template_path)
    
    # Define shapes and connectors
    shapes = [
        ShapeConfig(
            master_name="Rectangle",
            position=Point(1.0, 1.0),
            size=(2.0, 1.0),
            text="Shape 1"
        ),
        ShapeConfig(
            master_name="Rectangle",
            position=Point(4.0, 1.0),
            size=(2.0, 1.0),
            text="Shape 2"
        )
    ]
    
    connectors = [
        ConnectorConfig(
            from_shape="Rectangle",
            to_shape="Rectangle",
            style=ConnectorStyle.RIGHT_ANGLE,
            routing=ConnectorRouting.AVOID_SHAPES,
            color="255,0,0",
            thickness=2.0
        )
    ]
    
    # Mock Visio application
    with patch("win32com.client.Dispatch", return_value=mock_visio["app"]):
        result = await visio_service.generate_diagram(
            template_name=template_name,
            shapes=shapes,
            connectors=connectors,
            output_name="test_diagram",
            page_size=(8.5, 11.0),
            generate_pdf=True
        )
    
    # Verify result
    assert "visio_file" in result
    assert "pdf_file" in result
    assert Path(result["visio_file"]).name == "test_diagram.vsdx"
    assert Path(result["pdf_file"]).name == "test_diagram.pdf"

@pytest.mark.asyncio
async def test_generate_diagram_template_not_found(visio_service):
    shapes = [
        ShapeConfig(
            master_name="Rectangle",
            position=Point(1.0, 1.0)
        )
    ]
    
    with pytest.raises(VisioError) as exc_info:
        await visio_service.generate_diagram(
            template_name="nonexistent.vstx",
            shapes=shapes,
            connectors=[],
            output_name="test"
        )
    assert "Template not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_add_shape_with_properties(visio_service, mock_visio):
    shape_config = ShapeConfig(
        master_name="Rectangle",
        position=Point(1.0, 1.0),
        size=(2.0, 1.0),
        text="Test Shape",
        properties={
            "FillForegnd": "RGB(255,0,0)",
            "LineWeight": "2.0 pt"
        }
    )
    
    # Mock shape master
    mock_master = MagicMock()
    mock_visio["page"].Document.Masters.ItemU.return_value = mock_master
    
    shape = visio_service._add_shape(mock_visio["page"], shape_config)
    
    # Verify shape properties were set
    assert shape.Text == "Test Shape"
    assert shape.Cells("Width").FormulaU == "2.0 in"
    assert shape.Cells("Height").FormulaU == "1.0 in"
    assert shape.Cells("FillForegnd").FormulaU == "RGB(255,0,0)"
    assert shape.Cells("LineWeight").FormulaU == "2.0 pt"

@pytest.mark.asyncio
async def test_add_connector_with_routing(visio_service, mock_visio):
    connector_config = ConnectorConfig(
        from_shape="Shape1",
        to_shape="Shape2",
        style=ConnectorStyle.RIGHT_ANGLE,
        routing=ConnectorRouting.AVOID_SHAPES,
        color="255,0,0",
        thickness=2.0,
        pattern="2",
        begin_arrow="1",
        end_arrow="2"
    )
    
    # Mock shapes and connector master
    from_shape = MagicMock()
    to_shape = MagicMock()
    mock_visio["page"].Document.Masters.ItemU.return_value = MagicMock()
    
    connector = visio_service._add_connector(
        mock_visio["page"],
        from_shape,
        to_shape,
        connector_config
    )
    
    # Verify connector properties were set
    assert connector.Cells("RouteStyle").FormulaU == "16"  # Right angle
    assert connector.Cells("LineColor").FormulaU == "RGB(255,0,0)"
    assert connector.Cells("LineWeight").FormulaU == "2.0 pt"
    assert connector.Cells("LinePattern").FormulaU == "2"
    assert connector.Cells("BeginArrow").FormulaU == "1"
    assert connector.Cells("EndArrow").FormulaU == "2"

@pytest.mark.asyncio
async def test_network_flow_routing(visio_service, mock_visio):
    connector_config = ConnectorConfig(
        from_shape="Shape1",
        to_shape="Shape2",
        routing=ConnectorRouting.NETWORK_FLOW
    )
    
    # Mock shapes and connector
    from_shape = MagicMock()
    to_shape = MagicMock()
    connector = MagicMock()
    
    # Test network flow routing
    visio_service._apply_network_flow_routing(connector, mock_visio["page"])
    
    # Verify AutoRoute was called (placeholder implementation)
    assert connector.AutoRoute.called

@pytest.mark.asyncio
async def test_template_caching(visio_service, temp_dir):
    # Create test template
    template_name = "test.vstx"
    template_path = visio_service.template_dir / template_name
    create_test_template(template_path)
    
    # Get template path (should cache it)
    cached_path1 = await visio_service._get_template(template_name)
    assert cached_path1.exists()
    
    # Get template path again (should use cache)
    cached_path2 = await visio_service._get_template(template_name)
    assert cached_path2 == cached_path1 

@pytest.mark.asyncio
async def test_generate_diagram_with_internal_shapes(visio_service, temp_dir, mock_visio):
    # Create test template
    template_name = "test.vstx"
    template_path = visio_service.template_dir / template_name
    create_test_template(template_path)
    
    # Define shapes with internal components
    shapes = [
        ShapeConfig(
            master_name="Device",
            position=Point(1.0, 1.0),
            size=(3.0, 2.0),
            text="Device 1",
            internal_shapes=[
                InternalShape(
                    name="Port1",
                    relative_x=0.5,
                    relative_y=0.5,
                    width=0.8,
                    height=0.3,
                    text="Port 1"
                ),
                InternalShape(
                    name="Port2",
                    relative_x=0.5,
                    relative_y=1.2,
                    width=0.8,
                    height=0.3,
                    text="Port 2"
                )
            ]
        ),
        ShapeConfig(
            master_name="Device",
            position=Point(5.0, 1.0),
            size=(3.0, 2.0),
            text="Device 2",
            internal_shapes=[
                InternalShape(
                    name="Port1",
                    relative_x=0.5,
                    relative_y=0.5,
                    width=0.8,
                    height=0.3,
                    text="Port 1"
                )
            ]
        )
    ]
    
    # Define connections between internal shapes
    connectors = [
        ConnectorConfig(
            from_shape="Device",
            to_shape="Device",
            from_internal="Port1",  # Connect from Port1 of first device
            to_internal="Port1",    # Connect to Port1 of second device
            style=ConnectorStyle.RIGHT_ANGLE,
            routing=ConnectorRouting.AVOID_SHAPES,
            color="255,0,0",
            thickness=2.0
        )
    ]
    
    # Mock Visio application
    with patch("win32com.client.Dispatch", return_value=mock_visio["app"]):
        result = await visio_service.generate_diagram(
            template_name=template_name,
            shapes=shapes,
            connectors=connectors,
            output_name="test_diagram",
            page_size=(11.0, 8.5),
            generate_pdf=True
        )
    
    # Verify result
    assert "visio_file" in result
    assert "pdf_file" in result
    assert Path(result["visio_file"]).name == "test_diagram.vsdx"
    assert Path(result["pdf_file"]).name == "test_diagram.pdf"

@pytest.mark.asyncio
async def test_add_shape_with_internal_components(visio_service, mock_visio):
    shape_config = ShapeConfig(
        master_name="Device",
        position=Point(1.0, 1.0),
        size=(3.0, 2.0),
        text="Test Device",
        internal_shapes=[
            InternalShape(
                name="Port1",
                relative_x=0.5,
                relative_y=0.5,
                width=0.8,
                height=0.3,
                text="Port 1",
                properties={"LineWeight": "2.0 pt"}
            )
        ]
    )
    
    # Mock shape master and group operations
    mock_master = MagicMock()
    mock_visio["page"].Document.Masters.ItemU.return_value = mock_master
    mock_visio["page"].CreateSelection.return_value = MagicMock()
    mock_visio["page"].Application.Selection.Group.return_value = MagicMock()
    
    main_shape, internal_shapes = visio_service._add_shape(mock_visio["page"], shape_config)
    
    # Verify main shape was created
    assert main_shape is not None
    
    # Verify internal shapes were created
    assert "Port1" in internal_shapes
    internal_shape = internal_shapes["Port1"]
    assert internal_shape.Text == "Port 1"
    assert internal_shape.Cells("LineWeight").FormulaU == "2.0 pt"
    assert internal_shape.Cells("FillPattern").FormulaU == "0"  # No fill

@pytest.mark.asyncio
async def test_add_connector_between_internal_shapes(visio_service, mock_visio):
    connector_config = ConnectorConfig(
        from_shape="Device1",
        to_shape="Device2",
        from_internal="Port1",
        to_internal="Port2",
        style=ConnectorStyle.RIGHT_ANGLE,
        routing=ConnectorRouting.AVOID_SHAPES,
        color="255,0,0",
        thickness=2.0
    )
    
    # Mock shapes
    from_shape = MagicMock()
    to_shape = MagicMock()
    from_internal = MagicMock()
    to_internal = MagicMock()
    
    # Mock internal shape dictionaries
    from_internal_shapes = {"Port1": from_internal}
    to_internal_shapes = {"Port2": to_internal}
    
    # Mock connector master
    mock_visio["page"].Document.Masters.ItemU.return_value = MagicMock()
    
    connector = visio_service._add_connector(
        mock_visio["page"],
        from_shape,
        to_shape,
        from_internal_shapes,
        to_internal_shapes,
        connector_config
    )
    
    # Verify connector was created and connected to internal shapes
    assert connector is not None
    connector.Cells("BeginX").GlueTo.assert_called_with(from_internal.Cells("PinX"))
    connector.Cells("EndX").GlueTo.assert_called_with(to_internal.Cells("PinX"))

@pytest.mark.asyncio
async def test_add_connector_internal_shape_not_found(visio_service, mock_visio):
    connector_config = ConnectorConfig(
        from_shape="Device1",
        to_shape="Device2",
        from_internal="NonexistentPort",  # This port doesn't exist
        to_internal="Port2",
        style=ConnectorStyle.RIGHT_ANGLE
    )
    
    # Mock shapes
    from_shape = MagicMock()
    to_shape = MagicMock()
    to_internal = MagicMock()
    
    # Mock internal shape dictionaries
    from_internal_shapes = {}  # Empty dict to simulate missing internal shape
    to_internal_shapes = {"Port2": to_internal}
    
    # Test should raise VisioError
    with pytest.raises(VisioError) as exc_info:
        visio_service._add_connector(
            mock_visio["page"],
            from_shape,
            to_shape,
            from_internal_shapes,
            to_internal_shapes,
            connector_config
        )
    
    assert "Internal shape not found: NonexistentPort" in str(exc_info.value)

@pytest.mark.asyncio
async def test_add_shape_with_different_types(visio_service, mock_visio):
    # Test each internal shape type
    for shape_type in InternalShapeType:
        shape_config = ShapeConfig(
            master_name="Device",
            position=Point(1.0, 1.0),
            size=(3.0, 2.0),
            text=f"Test {shape_type.value}",
            internal_shapes=[
                InternalShape(
                    name="Component1",
                    relative_x=0.5,
                    relative_y=0.5,
                    width=0.8,
                    height=0.3,
                    shape_type=shape_type,
                    text=f"Test {shape_type.value}"
                )
            ]
        )
        
        # Mock shape creation methods
        mock_visio["page"].DrawRectangle.return_value = MagicMock()
        mock_visio["page"].DrawOval.return_value = MagicMock()
        mock_visio["page"].DrawQuarterArc.return_value = MagicMock()
        mock_visio["page"].DrawPolyline.return_value = MagicMock()
        
        main_shape, internal_shapes = visio_service._add_shape(mock_visio["page"], shape_config)
        
        # Verify shape was created
        assert main_shape is not None
        assert "Component1" in internal_shapes
        
        # Verify correct drawing method was called based on shape type
        if shape_type == InternalShapeType.RECTANGLE:
            assert mock_visio["page"].DrawRectangle.called
        elif shape_type == InternalShapeType.ELLIPSE:
            assert mock_visio["page"].DrawOval.called
        elif shape_type == InternalShapeType.DIAMOND:
            assert mock_visio["page"].DrawQuarterArc.called
        elif shape_type == InternalShapeType.HEXAGON:
            assert mock_visio["page"].DrawPolyline.called
        elif shape_type == InternalShapeType.TEXT:
            text_shape = mock_visio["page"].DrawRectangle.return_value
            assert text_shape.Cells("LinePattern").FormulaU == "0"

@pytest.mark.asyncio
async def test_add_shape_with_connection_points(visio_service, mock_visio):
    shape_config = ShapeConfig(
        master_name="Device",
        position=Point(1.0, 1.0),
        size=(3.0, 2.0),
        internal_shapes=[
            InternalShape(
                name="Port1",
                relative_x=0.5,
                relative_y=0.5,
                width=0.8,
                height=0.3,
                text="Port 1",
                connection_points=[
                    ConnectionPoint.LEFT,
                    ConnectionPoint.RIGHT,
                    ConnectionPoint.TOP
                ]
            )
        ]
    )
    
    # Mock shape and cells
    mock_shape = MagicMock()
    mock_visio["page"].DrawRectangle.return_value = mock_shape
    
    main_shape, internal_shapes = visio_service._add_shape(mock_visio["page"], shape_config)
    
    # Verify connection points were added
    port_shape = internal_shapes["Port1"]
    assert port_shape.CellsSRC.call_count == 6  # 2 calls per connection point

@pytest.mark.asyncio
async def test_add_connector_with_connection_points(visio_service, mock_visio):
    connector_config = ConnectorConfig(
        from_shape="Device1",
        to_shape="Device2",
        from_internal="Port1",
        to_internal="Port2",
        from_connection_point=ConnectionPoint.RIGHT,
        to_connection_point=ConnectionPoint.LEFT,
        style=ConnectorStyle.RIGHT_ANGLE
    )
    
    # Mock shapes and connection points
    from_shape = MagicMock()
    to_shape = MagicMock()
    from_internal = MagicMock()
    to_internal = MagicMock()
    
    # Mock connection point cells
    from_cell = MagicMock()
    to_cell = MagicMock()
    from_internal.Cells.return_value = from_cell
    to_internal.Cells.return_value = to_cell
    
    from_internal_shapes = {"Port1": from_internal}
    to_internal_shapes = {"Port2": to_internal}
    
    connector = visio_service._add_connector(
        mock_visio["page"],
        from_shape,
        to_shape,
        from_internal_shapes,
        to_internal_shapes,
        connector_config
    )
    
    # Verify connector was created with correct connection points
    assert connector is not None
    from_internal.Cells.assert_called_with("Connections.X2")  # Right connection point
    to_internal.Cells.assert_called_with("Connections.X1")    # Left connection point

@pytest.mark.asyncio
async def test_network_flow_routing(visio_service, mock_visio):
    # Create test connectors with intersecting paths
    mock_connector1 = MagicMock()
    mock_connector1.Cells.return_value.Result.return_value = 1.0
    mock_connector2 = MagicMock()
    mock_connector2.Cells.return_value.Result.return_value = 2.0
    
    # Mock page shapes
    mock_visio["page"].Shapes = [mock_connector1, mock_connector2]
    mock_visio["page"].Drop.return_value = MagicMock()
    
    connector_config = ConnectorConfig(
        from_shape="Device1",
        to_shape="Device2",
        routing=ConnectorRouting.NETWORK_FLOW
    )
    
    # Add connector with network flow routing
    connector = visio_service._add_connector(
        mock_visio["page"],
        MagicMock(),
        MagicMock(),
        {},
        {},
        connector_config
    )
    
    # Verify routing was applied
    assert connector.AddSection.called
    assert connector.Cells.call_count > 0

def test_calculate_hexagon_points(visio_service):
    points = visio_service._calculate_hexagon_points(1.0, 1.0, 2.0, 1.0)
    assert len(points) == 6  # Hexagon has 6 points
    
    # Verify points form a hexagon
    # Center points (left and right)
    assert points[0] == (1.0, 1.5)  # Left point
    assert points[3] == (3.0, 1.5)  # Right point
    
    # Top points
    assert 1.0 < points[1][0] < 2.0  # Top left x
    assert points[1][1] == 1.0       # Top left y
    assert 2.0 < points[2][0] < 3.0  # Top right x
    assert points[2][1] == 1.0       # Top right y
    
    # Bottom points
    assert 1.0 < points[5][0] < 2.0  # Bottom left x
    assert points[5][1] == 2.0       # Bottom left y
    assert 2.0 < points[4][0] < 3.0  # Bottom right x
    assert points[4][1] == 2.0       # Bottom right y

def test_line_intersection(visio_service):
    # Test intersecting lines
    p1 = (0.0, 0.0)
    p2 = (2.0, 2.0)
    p3 = (0.0, 2.0)
    p4 = (2.0, 0.0)
    
    intersection = visio_service._line_intersection(p1, p2, p3, p4)
    assert intersection is not None
    assert intersection[0] == 1.0
    assert intersection[1] == 1.0
    
    # Test parallel lines
    p5 = (0.0, 0.0)
    p6 = (2.0, 0.0)
    p7 = (0.0, 1.0)
    p8 = (2.0, 1.0)
    
    intersection = visio_service._line_intersection(p5, p6, p7, p8)
    assert intersection is None
    
    # Test non-intersecting lines
    p9 = (0.0, 0.0)
    p10 = (1.0, 1.0)
    p11 = (3.0, 0.0)
    p12 = (4.0, 1.0)
    
    intersection = visio_service._line_intersection(p9, p10, p11, p12)
    assert intersection is None

def test_add_custom_connection_point(mock_shape):
    """Test adding a custom connection point to a shape"""
    service = VisioGenerationService("/templates", "/output")
    custom_point = CustomConnectionPoint(
        name="custom1",
        relative_x=0.25,
        relative_y=0.75,
        angle=45
    )
    
    service._add_connection_point(mock_shape, custom_point)
    
    # Verify the connection point was added with correct coordinates and angle
    mock_shape.CellsSRC.assert_any_call(7, 0, 0)  # X position
    mock_shape.CellsSRC.assert_any_call(7, 0, 1)  # Y position
    mock_shape.CellsSRC.assert_any_call(7, 0, 4)  # Angle
    
    # Verify the formulas were set correctly
    mock_shape.CellsSRC.return_value.FormulaU = "0.25"  # X
    mock_shape.CellsSRC.return_value.FormulaU = "0.75"  # Y
    mock_shape.CellsSRC.return_value.FormulaU = "45deg" # Angle

def test_apply_valid_shape_style(visio_service, mock_visio):
    """Test applying valid shape style properties"""
    _, _, _, mock_shape = mock_visio
    
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
    
    visio_service._apply_shape_style(mock_shape, style)
    
    # Verify color conversions and applications
    assert mock_shape.FillForegnd == visio_service._rgb_to_visio_color(255, 0, 0)
    assert mock_shape.LineColor == visio_service._rgb_to_visio_color(0, 255, 0)
    assert mock_shape.CharColor == visio_service._rgb_to_visio_color(0, 0, 255)
    
    # Verify other properties
    assert mock_shape.LineWeight == 2.0
    assert mock_shape.CharSize == "12.0 pt"
    assert mock_shape.FillForegndTrans == 0.2  # 1.0 - opacity
    assert mock_shape.CharFont == "Arial"
    assert mock_shape.CharStyle == 3  # Bold (1) + Italic (2)

def test_apply_invalid_shape_style(visio_service, mock_visio):
    """Test applying invalid shape style properties"""
    _, _, _, mock_shape = mock_visio
    
    invalid_style = {
        "fill_color": "256,0,0",  # Invalid RGB
        "line_weight": -1,        # Invalid weight
        "opacity": 2.0,           # Invalid opacity
        "font_name": "NonexistentFont",  # Invalid font
        "text_style": "Invalid"   # Invalid style
    }
    
    with pytest.raises(VisioGenerationError) as exc_info:
        visio_service._apply_shape_style(mock_shape, invalid_style)
    
    error_msg = str(exc_info.value)
    assert "Invalid shape style properties" in error_msg
    assert "invalid_rgb_range" in error_msg
    assert "below_minimum" in error_msg
    assert "above_maximum" in error_msg
    assert "unavailable_font" in error_msg
    assert "invalid_text_style" in error_msg

def test_color_format_handling(visio_service, mock_visio):
    """Test handling of different color formats"""
    _, _, _, mock_shape = mock_visio
    
    # Test RGB format
    style = {"fill_color": "255,0,0"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.FillForegnd == visio_service._rgb_to_visio_color(255, 0, 0)
    
    # Test HEX format
    style = {"fill_color": "#00FF00"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.FillForegnd == visio_service._rgb_to_visio_color(0, 255, 0)
    
    # Test HTML color name
    style = {"fill_color": "blue"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.FillForegnd == visio_service._rgb_to_visio_color(0, 0, 255)

def test_text_style_combinations(visio_service, mock_visio):
    """Test different combinations of text styles"""
    _, _, _, mock_shape = mock_visio
    
    # Test Bold only
    style = {"text_style": "Bold"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.CharStyle == 1
    
    # Test Italic only
    style = {"text_style": "Italic"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.CharStyle == 2
    
    # Test Bold + Italic
    style = {"text_style": "Bold,Italic"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.CharStyle == 3
    
    # Test Bold + Italic + Underline
    style = {"text_style": "Bold,Italic,Underline"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.CharStyle == 7

def test_font_handling(visio_service, mock_visio):
    """Test font handling and validation"""
    _, _, _, mock_shape = mock_visio
    
    # Test valid font
    style = {"font_name": "Arial"}
    visio_service._apply_shape_style(mock_shape, style)
    assert mock_shape.CharFont == "Arial"
    
    # Test invalid font
    style = {"font_name": "NonexistentFont"}
    with pytest.raises(VisioGenerationError) as exc_info:
        visio_service._apply_shape_style(mock_shape, style)
    assert "unavailable_font" in str(exc_info.value)

def test_error_handling(visio_service, mock_visio):
    """Test error handling for Visio API failures"""
    _, _, _, mock_shape = mock_visio
    
    # Simulate Visio API error
    mock_shape.FillForegnd = MagicMock(side_effect=Exception("Visio API Error"))
    
    style = {"fill_color": "255,0,0"}
    with pytest.raises(VisioGenerationError) as exc_info:
        visio_service._apply_shape_style(mock_shape, style)
    assert "Failed to apply style property" in str(exc_info.value)
    assert "Visio API Error" in str(exc_info.value)

def test_rgb_to_visio_color(visio_service):
    """Test RGB to Visio color conversion"""
    assert visio_service._rgb_to_visio_color(255, 0, 0) == 255  # Red
    assert visio_service._rgb_to_visio_color(0, 255, 0) == 65280  # Green
    assert visio_service._rgb_to_visio_color(0, 0, 255) == 16711680  # Blue
    assert visio_service._rgb_to_visio_color(255, 255, 255) == 16777215  # White 

def test_multi_page_features(visio_service, mock_win32com, mock_pythoncom):
    """Test multi-page features including page ordering, themes, and margins"""
    # Test data
    pages = [
        PageConfig(
            name="Page 2",
            page_number=2,
            shapes=[
                VisioShape(
                    shape_type="Rectangle",
                    name="Shape2",
                    x=1.0,
                    y=1.0
                )
            ],
            connectors=[],
            theme="modern",
            margin=(0.5, 0.5, 0.5, 0.5),
            scale=1.5,
            grid_visible=False
        ),
        PageConfig(
            name="Page 1",
            page_number=1,
            shapes=[
                VisioShape(
                    shape_type="Rectangle",
                    name="Shape1",
                    x=1.0,
                    y=1.0
                )
            ],
            connectors=[],
            orientation="landscape",
            guides_visible=False
        )
    ]
    
    # Generate diagram
    visio_path, pdf_path = visio_service.generate_diagram(
        template_name="test",
        pages=pages,
        output_dir=Path("output"),
        filename="test_multi_page"
    )
    
    # Verify paths
    assert visio_path == Path("output") / "test_multi_page.vsdx"
    assert pdf_path == Path("output") / "test_multi_page.pdf"
    
    # Verify page ordering
    mock_doc = mock_win32com.return_value.Documents.Add.return_value
    page_names = [p.Name for p in mock_doc.Pages]
    assert page_names == ["Page 1", "Page 2"]
    
    # Verify page properties were set
    page1 = mock_doc.Pages.Item("Page 1")
    assert page1.PageSheet.CellsSRC(1, 2, 2).FormulaU == "1"  # Landscape
    assert page1.PageSheet.CellsSRC(1, 2, 8).FormulaU == "0"  # Guides hidden
    
    page2 = mock_doc.Pages.Item("Page 2")
    assert page2.PageSheet.CellsSRC(1, 2, 5).FormulaU == "1.5"  # Scale
    assert page2.PageSheet.CellsSRC(1, 2, 7).FormulaU == "0"  # Grid hidden
    assert page2.PageSheet.CellsSRC(1, 2, 3).FormulaU == "0.5 in"  # Left margin
    
    # Verify theme was applied
    theme_path = visio_service.templates_dir / "themes" / "modern.vst"
    page2.ApplyTheme.assert_called_once_with(str(theme_path))
    
    # Verify COM operations
    mock_win32com.assert_called_once()
    mock_pythoncom[0].assert_called_once()  # CoInitialize
    mock_pythoncom[1].assert_called_once()  # CoUninitialize 