from typing import Dict
from src.models.diagram import Shape

class ShapeMetadataExtractor:
    """Extracts text and metadata from shapes"""
    def __init__(self):
        self.text_recognizer = TextRecognizer()
        
    def extract_metadata(self, shape: Shape) -> Dict:
        """Extract metadata from a shape"""
        text = self.text_recognizer.recognize(shape.image)
        return {
            "text": text,
            "properties": self._extract_properties(text),
            "connections": shape.connections
        }
        
    def _extract_properties(self, text: str) -> Dict:
        """Extract properties from shape text"""
        # Implement property extraction logic
        return {} 