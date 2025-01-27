import pytest
from unittest.mock import Mock, patch, MagicMock
import io
from PIL import Image
import numpy as np
from datetime import datetime
import cv2

from src.services.screenshot_service import (
    ScreenshotService,
    Screenshot,
    ScreenRegion,
    VisualDifference
)
from src.services.ai_service_config import AIServiceManager
from src.services.rag_memory_service import RAGMemoryService

@pytest.fixture
def mock_mss():
    with patch('mss.mss') as mss_mock:
        # Mock screen capture
        mss = MagicMock()
        mss_mock.return_value = mss
        
        # Mock screenshot
        screenshot = MagicMock()
        screenshot.size = (1920, 1080)
        screenshot.width = 1920
        screenshot.height = 1080
        screenshot.rgb = b"test_image_data"
        
        # Mock grab operation
        mss.grab.return_value = screenshot
        
        # Mock monitors
        mss.monitors = [{"left": 0, "top": 0, "width": 1920, "height": 1080}]
        
        yield mss

@pytest.fixture
def mock_ai_provider():
    provider = MagicMock()
    provider.analyze_image.return_value = "Test OCR text"
    return provider

@pytest.fixture
def mock_ai_service_manager(mock_ai_provider):
    manager = MagicMock(spec=AIServiceManager)
    manager.get_provider.return_value = mock_ai_provider
    return manager

@pytest.fixture
def mock_rag_memory():
    memory = MagicMock(spec=RAGMemoryService)
    memory.store_image.return_value = "test_id"
    return memory

@pytest.fixture
def screenshot_service(mock_mss, mock_ai_service_manager, mock_rag_memory):
    return ScreenshotService(
        ai_service_manager=mock_ai_service_manager,
        rag_memory=mock_rag_memory
    )

def test_capture_screen_full(screenshot_service, mock_mss):
    # Capture full screen
    screenshot = screenshot_service.capture_screen()
    
    # Verify operations
    mock_mss.grab.assert_called_once()
    assert isinstance(screenshot, Screenshot)
    assert screenshot.width == 1920
    assert screenshot.height == 1080
    assert screenshot.region is None

def test_capture_screen_region(screenshot_service, mock_mss):
    # Test data
    region = ScreenRegion(
        left=100,
        top=100,
        width=800,
        height=600
    )
    
    # Capture region
    screenshot = screenshot_service.capture_screen(region)
    
    # Verify operations
    mock_mss.grab.assert_called_once_with({
        "left": 100,
        "top": 100,
        "width": 800,
        "height": 600
    })
    assert screenshot.region == region

def test_extract_text_pytesseract(screenshot_service):
    # Test data
    img = Image.new('RGB', (100, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    
    screenshot = Screenshot(
        image_data=img_bytes.getvalue(),
        format="PNG",
        width=100,
        height=100,
        timestamp=datetime.utcnow()
    )
    
    # Extract text using default provider
    with patch('pytesseract.image_to_string') as mock_pytesseract:
        mock_pytesseract.return_value = "Test OCR text"
        text = screenshot_service.extract_text(screenshot)
    
    # Verify operations
    assert text == "Test OCR text"
    mock_pytesseract.assert_called_once()

def test_extract_text_ai_service(screenshot_service, mock_ai_provider):
    # Test data
    screenshot = Screenshot(
        image_data=b"test_image",
        format="PNG",
        width=100,
        height=100,
        timestamp=datetime.utcnow()
    )
    
    # Configure service to use AI provider
    screenshot_service.ocr_provider = "test_provider"
    
    # Extract text
    text = screenshot_service.extract_text(screenshot)
    
    # Verify operations
    assert text == "Test OCR text"
    mock_ai_provider.analyze_image.assert_called_once()

def test_compare_screenshots(screenshot_service):
    # Create test images
    img1 = np.zeros((100, 100, 3), dtype=np.uint8)
    img2 = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(img2, (10, 10), (50, 50), (255, 255, 255), -1)  # Add white rectangle
    
    # Convert to bytes
    _, img1_bytes = cv2.imencode(".png", img1)
    _, img2_bytes = cv2.imencode(".png", img2)
    
    # Create screenshots
    screenshot1 = Screenshot(
        image_data=img1_bytes.tobytes(),
        format="PNG",
        width=100,
        height=100,
        timestamp=datetime.utcnow()
    )
    
    screenshot2 = Screenshot(
        image_data=img2_bytes.tobytes(),
        format="PNG",
        width=100,
        height=100,
        timestamp=datetime.utcnow()
    )
    
    # Compare screenshots
    diff = screenshot_service.compare_screenshots(screenshot1, screenshot2)
    
    # Verify results
    assert isinstance(diff, VisualDifference)
    assert diff.diff_score > 0
    assert len(diff.changed_regions) == 1
    assert isinstance(diff.diff_image, bytes)

def test_store_screenshot(screenshot_service, mock_rag_memory):
    # Test data
    screenshot = Screenshot(
        image_data=b"test_image",
        format="PNG",
        width=100,
        height=100,
        timestamp=datetime.utcnow(),
        metadata={"test": "metadata"}
    )
    
    # Store screenshot
    entry_id = screenshot_service.store_screenshot(screenshot)
    
    # Verify operations
    assert entry_id == "test_id"
    mock_rag_memory.store_image.assert_called_once()

def test_store_screenshot_with_text(screenshot_service, mock_rag_memory):
    # Test data
    screenshot = Screenshot(
        image_data=b"test_image",
        format="PNG",
        width=100,
        height=100,
        timestamp=datetime.utcnow()
    )
    
    # Configure pytesseract mock
    with patch('pytesseract.image_to_string') as mock_pytesseract:
        mock_pytesseract.return_value = "Test OCR text"
        
        # Store screenshot with text extraction
        entry_id = screenshot_service.store_screenshot(screenshot, extract_text=True)
    
    # Verify operations
    assert entry_id == "test_id"
    mock_rag_memory.store_image.assert_called_once()
    mock_rag_memory.update_metadata.assert_called_once()

def test_monitor_visual_changes(screenshot_service):
    # Mock time.sleep to avoid actual waiting
    with patch('time.sleep'):
        # Configure callback
        callback = MagicMock()
        
        # Start monitoring with KeyboardInterrupt after first iteration
        with patch.object(screenshot_service, 'capture_screen') as mock_capture:
            # Create test screenshots
            img1 = np.zeros((100, 100, 3), dtype=np.uint8)
            img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
            
            # Convert to bytes
            _, img1_bytes = cv2.imencode(".png", img1)
            _, img2_bytes = cv2.imencode(".png", img2)
            
            # Configure mock to return different screenshots
            mock_capture.side_effect = [
                Screenshot(
                    image_data=img1_bytes.tobytes(),
                    format="PNG",
                    width=100,
                    height=100,
                    timestamp=datetime.utcnow()
                ),
                Screenshot(
                    image_data=img2_bytes.tobytes(),
                    format="PNG",
                    width=100,
                    height=100,
                    timestamp=datetime.utcnow()
                ),
                KeyboardInterrupt  # Stop after second screenshot
            ]
            
            # Monitor changes
            screenshot_service.monitor_visual_changes(callback=callback)
            
            # Verify operations
            assert mock_capture.call_count == 3
            callback.assert_called_once()

def test_error_handling(screenshot_service, mock_mss):
    # Configure mock to raise error
    mock_mss.grab.side_effect = Exception("Test error")
    
    # Test error handling
    with pytest.raises(Exception):
        screenshot_service.capture_screen()

def test_to_cv2_image(screenshot_service):
    # Create test image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_bytes = cv2.imencode(".png", img)
    
    # Convert to OpenCV format
    cv2_img = screenshot_service._to_cv2_image(img_bytes.tobytes())
    
    # Verify result
    assert isinstance(cv2_img, np.ndarray)
    assert cv2_img.shape == (100, 100, 3) 