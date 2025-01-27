import pytest
from pathlib import Path
import tempfile
import cv2
import numpy as np
from PIL import Image
from unittest.mock import Mock, AsyncMock, patch
from src.services.screenshot_analysis_service import (
    ScreenshotAnalysisService,
    ColorPalette,
    FontInfo,
    LogoDetection,
    VisualAnalysisResult,
    AnalysisError
)
from src.services.rag_memory_service import RAGMemoryService

@pytest.fixture
def sample_image():
    """Create a sample test image"""
    # Create a 300x200 test image with some shapes and text
    image = np.zeros((200, 300, 3), dtype=np.uint8)
    
    # Add background
    image[:, :] = [240, 240, 240]
    
    # Add some colored shapes
    cv2.rectangle(image, (50, 50), (100, 100), (0, 0, 255), -1)  # Red square
    cv2.circle(image, (200, 100), 30, (0, 255, 0), -1)  # Green circle
    
    # Add some text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, "Test Text", (80, 150), font, 1, (0, 0, 0), 2)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        cv2.imwrite(tmp.name, image)
        return Path(tmp.name)

@pytest.fixture
def logo_templates_dir():
    """Create a directory with sample logo templates"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple logo template
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        cv2.rectangle(template, (10, 10), (40, 40), (255, 0, 0), -1)
        
        template_path = Path(temp_dir) / "test_logo.png"
        cv2.imwrite(str(template_path), template)
        
        yield Path(temp_dir)

@pytest.fixture
async def analysis_service(logo_templates_dir):
    """Create a test screenshot analysis service"""
    rag_memory = Mock(spec=RAGMemoryService)
    rag_memory.query_memory = AsyncMock(return_value=None)
    rag_memory.store_entry = AsyncMock()
    
    service = ScreenshotAnalysisService(
        rag_memory=rag_memory,
        logo_templates_dir=logo_templates_dir
    )
    
    return service

@pytest.mark.asyncio
async def test_analyze_screenshot(analysis_service, sample_image):
    """Test complete screenshot analysis"""
    result = await analysis_service.analyze_screenshot(sample_image)
    
    assert isinstance(result, VisualAnalysisResult)
    assert result.image_hash is not None
    assert isinstance(result.color_palette, ColorPalette)
    assert isinstance(result.font_info, FontInfo)
    assert isinstance(result.detected_logos, list)
    assert isinstance(result.symbols, list)
    assert isinstance(result.layout_info, dict)

@pytest.mark.asyncio
async def test_analyze_screenshot_cached(analysis_service, sample_image):
    """Test using cached analysis results"""
    # Mock cached result
    cached_result = {
        "image_hash": "test_hash",
        "color_palette": {
            "primary_colors": [(255, 255, 255)],
            "secondary_colors": [(0, 0, 0)],
            "background_color": (255, 255, 255),
            "accent_colors": [(128, 128, 128)],
            "color_distribution": {"(255, 255, 255)": 0.8}
        },
        "font_info": {
            "font_sizes": [12],
            "font_families": ["sans-serif"],
            "text_colors": [(0, 0, 0)],
            "heading_fonts": ["sans-serif"],
            "body_fonts": ["sans-serif"],
            "is_serif": False,
            "confidence": 0.8
        },
        "detected_logos": [],
        "symbols": [],
        "layout_info": {},
        "processing_time_ms": 100.0
    }
    
    analysis_service.rag_memory.query_memory.return_value = [{
        "content": cached_result
    }]
    
    result = await analysis_service.analyze_screenshot(sample_image)
    assert result.image_hash == "test_hash"
    assert analysis_service.rag_memory.store_entry.call_count == 0

@pytest.mark.asyncio
async def test_extract_color_palette(analysis_service, sample_image):
    """Test color palette extraction"""
    image = cv2.imread(str(sample_image))
    palette = analysis_service._extract_color_palette(image)
    
    assert isinstance(palette, ColorPalette)
    assert len(palette.primary_colors) == 2
    assert len(palette.secondary_colors) == 2
    assert isinstance(palette.background_color, tuple)
    assert sum(palette.color_distribution.values()) == pytest.approx(1.0)

@pytest.mark.asyncio
async def test_extract_font_info(analysis_service, sample_image):
    """Test font information extraction"""
    image = cv2.imread(str(sample_image))
    font_info = analysis_service._extract_font_info(image)
    
    assert isinstance(font_info, FontInfo)
    assert isinstance(font_info.font_sizes, list)
    assert isinstance(font_info.text_colors, list)
    assert isinstance(font_info.is_serif, bool)
    assert 0 <= font_info.confidence <= 1

@pytest.mark.asyncio
async def test_detect_logos(analysis_service, sample_image):
    """Test logo detection"""
    image = cv2.imread(str(sample_image))
    logos = analysis_service._detect_logos(image)
    
    assert isinstance(logos, list)
    for logo in logos:
        assert isinstance(logo, LogoDetection)
        assert len(logo.bounding_box) == 4
        assert 0 <= logo.confidence <= 1

@pytest.mark.asyncio
async def test_detect_symbols(analysis_service, sample_image):
    """Test symbol detection"""
    image = cv2.imread(str(sample_image))
    symbols = analysis_service._detect_symbols(image)
    
    assert isinstance(symbols, list)
    for symbol in symbols:
        assert "bounding_box" in symbol
        assert "area" in symbol
        assert "symmetry_score" in symbol
        assert 0 <= symbol["symmetry_score"] <= 1

@pytest.mark.asyncio
async def test_analyze_layout(analysis_service, sample_image):
    """Test layout analysis"""
    image = cv2.imread(str(sample_image))
    layout = analysis_service._analyze_layout(image)
    
    assert isinstance(layout, dict)
    assert "image_size" in layout
    assert "aspect_ratio" in layout
    assert "grid_score" in layout
    assert 0 <= layout["grid_score"] <= 1

@pytest.mark.asyncio
async def test_invalid_image(analysis_service):
    """Test handling invalid image"""
    with pytest.raises(AnalysisError):
        await analysis_service.analyze_screenshot(Path("nonexistent.png"))

@pytest.mark.asyncio
async def test_calculate_symmetry(analysis_service):
    """Test symmetry calculation"""
    # Create symmetric test image
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(image, (25, 25), (75, 75), (255, 255, 255), -1)
    
    symmetry = analysis_service._calculate_symmetry(image)
    assert 0 <= symmetry <= 1
    assert symmetry > 0.8  # Should be highly symmetric

@pytest.mark.asyncio
async def test_check_layout_symmetry(analysis_service):
    """Test layout symmetry check"""
    # Create symmetric test image
    image = np.zeros((100, 100), dtype=np.uint8)
    cv2.line(image, (50, 0), (50, 100), 255, 2)
    cv2.line(image, (0, 50), (100, 50), 255, 2)
    
    symmetry = analysis_service._check_layout_symmetry(image)
    assert 0 <= symmetry <= 1
    assert symmetry > 0.8  # Should be highly symmetric

@pytest.mark.asyncio
async def test_calculate_grid_score(analysis_service):
    """Test grid score calculation"""
    horizontal_lines = [(0, 25, 100, 25), (0, 75, 100, 75)]
    vertical_lines = [(25, 0, 25, 100), (75, 0, 75, 100)]
    
    score = analysis_service._calculate_grid_score(
        horizontal_lines,
        vertical_lines,
        100,
        100
    )
    
    assert 0 <= score <= 1
    assert score > 0  # Should detect grid pattern 