import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import cv2
import mss
import mss.tools
from PIL import Image
import io
import pytesseract
from datetime import datetime
from .ai_service_config import AIServiceManager
from .rag_memory_service import RAGMemoryService
from .exceptions import ScreenshotError

logger = logging.getLogger(__name__)

@dataclass
class ScreenRegion:
    """Represents a region of the screen to capture"""
    left: int
    top: int
    width: int
    height: int

@dataclass
class Screenshot:
    """Represents a captured screenshot"""
    image_data: bytes
    format: str
    width: int
    height: int
    timestamp: datetime
    region: Optional[ScreenRegion] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class VisualDifference:
    """Represents visual differences between screenshots"""
    diff_image: bytes
    diff_score: float
    changed_regions: List[ScreenRegion]
    timestamp: datetime

class ScreenshotService:
    """Service for capturing and analyzing screenshots"""
    
    def __init__(
        self,
        ai_service_manager: AIServiceManager,
        rag_memory: RAGMemoryService,
        ocr_provider: str = "default",
        diff_threshold: float = 0.1
    ):
        self.ai_service_manager = ai_service_manager
        self.rag_memory = rag_memory
        self.ocr_provider = ocr_provider
        self.diff_threshold = diff_threshold
        self.mss = mss.mss()
        
        logger.info("Initialized screenshot service")
    
    def capture_screen(
        self,
        region: Optional[ScreenRegion] = None,
        format: str = "PNG"
    ) -> Screenshot:
        """Captures a screenshot of the entire screen or specified region"""
        try:
            # Prepare capture region
            if region:
                monitor = {
                    "left": region.left,
                    "top": region.top,
                    "width": region.width,
                    "height": region.height
                }
            else:
                monitor = self.mss.monitors[0]  # Primary monitor
            
            # Capture screenshot
            screenshot = self.mss.grab(monitor)
            
            # Convert to bytes
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            img_bytes = io.BytesIO()
            img.save(img_bytes, format=format)
            
            # Create Screenshot object
            result = Screenshot(
                image_data=img_bytes.getvalue(),
                format=format,
                width=screenshot.width,
                height=screenshot.height,
                timestamp=datetime.utcnow(),
                region=region,
                metadata={"source": "screen_capture"}
            )
            
            logger.info(f"Captured screenshot: {result.width}x{result.height}")
            return result
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            raise
    
    def extract_text(
        self,
        screenshot: Screenshot,
        lang: str = "eng"
    ) -> str:
        """Extracts text from screenshot using OCR"""
        try:
            if self.ocr_provider == "default":
                # Use pytesseract
                img = Image.open(io.BytesIO(screenshot.image_data))
                text = pytesseract.image_to_string(img, lang=lang)
            else:
                # Use configured AI service
                provider = self.ai_service_manager.get_provider(self.ocr_provider)
                text = provider.analyze_image(
                    image_data=screenshot.image_data,
                    prompt="Extract all text from this image"
                )
            
            logger.info(f"Extracted {len(text.split())} words from screenshot")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise
    
    def compare_screenshots(
        self,
        screenshot1: Screenshot,
        screenshot2: Screenshot
    ) -> VisualDifference:
        """Compares two screenshots and identifies differences"""
        try:
            # Convert screenshots to numpy arrays
            img1 = self._to_cv2_image(screenshot1.image_data)
            img2 = self._to_cv2_image(screenshot2.image_data)
            
            # Ensure same size
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
            
            # Calculate difference
            diff = cv2.absdiff(img1, img2)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            
            # Find changed regions
            contours, _ = cv2.findContours(
                thresh,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            # Calculate difference score
            diff_score = np.sum(thresh) / (thresh.shape[0] * thresh.shape[1] * 255)
            
            # Get changed regions
            changed_regions = []
            for contour in contours:
                if cv2.contourArea(contour) > 100:  # Filter small changes
                    x, y, w, h = cv2.boundingRect(contour)
                    changed_regions.append(ScreenRegion(
                        left=x,
                        top=y,
                        width=w,
                        height=h
                    ))
            
            # Create difference visualization
            diff_img = img1.copy()
            cv2.drawContours(diff_img, contours, -1, (0, 0, 255), 2)
            
            # Convert diff image to bytes
            diff_bytes = cv2.imencode(".png", diff_img)[1].tobytes()
            
            # Create VisualDifference object
            result = VisualDifference(
                diff_image=diff_bytes,
                diff_score=diff_score,
                changed_regions=changed_regions,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Found {len(changed_regions)} changed regions, diff score: {diff_score:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {str(e)}")
            raise
    
    def store_screenshot(
        self,
        screenshot: Screenshot,
        extract_text: bool = True,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Stores screenshot in RAG memory"""
        try:
            # Extract text if requested
            text_content = None
            if extract_text:
                text_content = self.extract_text(screenshot)
            
            # Prepare metadata
            metadata = {
                "width": screenshot.width,
                "height": screenshot.height,
                "format": screenshot.format,
                "timestamp": screenshot.timestamp.isoformat(),
                "source": "screenshot_service"
            }
            
            if screenshot.region:
                metadata["region"] = {
                    "left": screenshot.region.left,
                    "top": screenshot.region.top,
                    "width": screenshot.region.width,
                    "height": screenshot.region.height
                }
            
            if additional_metadata:
                metadata.update(additional_metadata)
            
            # Store in RAG memory
            entry_id = self.rag_memory.store_image(
                image_data=screenshot.image_data,
                metadata=metadata,
                extract_text=False  # We already extracted text
            )
            
            # Update text content if extracted
            if text_content:
                self.rag_memory.update_metadata(
                    entry_id=entry_id,
                    metadata={
                        **metadata,
                        "ocr_text": text_content
                    }
                )
            
            logger.info(f"Stored screenshot in RAG memory with ID: {entry_id}")
            return entry_id
            
        except Exception as e:
            logger.error(f"Error storing screenshot: {str(e)}")
            raise ScreenshotError(f"Failed to store screenshot: {str(e)}")
    
    def monitor_visual_changes(
        self,
        region: Optional[ScreenRegion] = None,
        interval_seconds: float = 1.0,
        callback: Optional[callable] = None
    ):
        """Monitors screen for visual changes"""
        try:
            import time
            
            logger.info("Starting visual change monitoring")
            last_screenshot = self.capture_screen(region)
            
            while True:
                time.sleep(interval_seconds)
                
                # Capture new screenshot
                current_screenshot = self.capture_screen(region)
                
                # Compare screenshots
                diff = self.compare_screenshots(last_screenshot, current_screenshot)
                
                # Check if significant changes
                if diff.diff_score > self.diff_threshold:
                    logger.info(f"Detected visual change: {diff.diff_score:.3f}")
                    
                    # Store screenshots and difference
                    diff_id = self.store_screenshot(
                        Screenshot(
                            image_data=diff.diff_image,
                            format="PNG",
                            width=current_screenshot.width,
                            height=current_screenshot.height,
                            timestamp=diff.timestamp,
                            region=region,
                            metadata={
                                "type": "visual_diff",
                                "diff_score": diff.diff_score,
                                "changed_regions": [
                                    {
                                        "left": r.left,
                                        "top": r.top,
                                        "width": r.width,
                                        "height": r.height
                                    }
                                    for r in diff.changed_regions
                                ]
                            }
                        )
                    )
                    
                    # Call callback if provided
                    if callback:
                        callback(diff, diff_id)
                
                last_screenshot = current_screenshot
                
        except KeyboardInterrupt:
            logger.info("Stopped visual change monitoring")
        except Exception as e:
            logger.error(f"Error monitoring visual changes: {str(e)}")
            raise
    
    def _to_cv2_image(self, image_data: bytes) -> np.ndarray:
        """Converts image bytes to OpenCV format"""
        nparr = np.frombuffer(image_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR) 