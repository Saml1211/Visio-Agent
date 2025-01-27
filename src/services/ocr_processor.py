import pytesseract
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from PIL import Image, ImageEnhance
from typing import Optional
from tenacity import retry, wait_exponential
import logging

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Multi-engine OCR processor with fallback capabilities"""
    
    def __init__(self, azure_client: Optional[ComputerVisionClient] = None):
        self.azure = azure_client
        
    def enhanced_ocr(self, image: Image, use_azure: bool = False) -> str:
        """Perform OCR with best available engine"""
        if use_azure and self.azure:
            return self._azure_ocr(image)
        return pytesseract.image_to_string(
            image, 
            config='--psm 11 --oem 3',
            lang='eng+equ'
        )
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
    def _azure_ocr(self, image: Image) -> str:
        """Azure OCR with exponential backoff"""
        result = self.azure.recognize_printed_text_in_stream(image.tobytes())
        return ' '.join([line.text for line in result.regions[0].lines])

def preprocess_image(image_path):
    """Add error handling and image validation"""
    try:
        # Set Tesseract path for macOS ARM64
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        
        img = Image.open(image_path)
        # Convert to grayscale and enhance contrast
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        return img
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        raise OCRProcessingError("Invalid image format or corrupted file") from e 