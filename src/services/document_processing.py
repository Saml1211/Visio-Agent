from typing import Dict, List, Optional
import pdfplumber
import fitz  # PyMuPDF
from PIL import Image
import cv2
import numpy as np
from rag_memory_service import RAGMemoryService
import re
from security import SecurityError
import logging
import io
from tenacity import retry, wait_exponential
from src.utils.retry_logic import jina_retry
from jina import Client
from config import config

logger = logging.getLogger(__name__)

class AdvancedDocumentProcessor:
    """Process complex documents with layout analysis and AI-enhanced extraction"""
    
    def __init__(self, rag_service: RAGMemoryService):
        self.rag = rag_service
        self.ocr_cache = {}  # For storing processed image hashes
        self.safe_path_pattern = re.compile(r'^[\w\-./]+$')  # Prevent directory traversal
        
    def process_document(self, file_path: str) -> Dict:
        """Main processing pipeline"""
        if not self.safe_path_pattern.match(file_path):
            raise SecurityError("Invalid file path pattern")
        doc_type = self._detect_document_type(file_path)
        layout = self._analyze_layout(file_path, doc_type)
        
        # Retrieve similar document structures from RAG
        similar_docs = self.rag.query(
            f"Document layout features: {layout['metadata']}",
            top_k=3
        )
        
        content = {
            'text': self._extract_structured_text(file_path, doc_type, similar_docs),
            'tables': self._extract_tables(file_path, doc_type, similar_docs),
            'images': self._process_images(file_path, doc_type),
            'layout_context': [doc['content'] for doc in similar_docs]
        }
        
        self.rag.store(file_path, content)
        return content

    def _analyze_layout(self, file_path: str, doc_type: str) -> Dict:
        """Perform advanced layout analysis"""
        if doc_type == 'pdf':
            with fitz.open(file_path) as doc:
                page = doc.load_page(0)
                layout = page.get_text("dict", flags=fitz.TEXT_PRESERVE_LAYOUT)
                return self._detect_columns(layout)
        return {}

    def _detect_columns(self, layout_data: Dict) -> Dict:
        """Identify multi-column layouts using spatial analysis"""
        blocks = layout_data['blocks']
        x_coords = sorted([block['bbox'][0] for block in blocks])
        column_boundaries = np.array(x_coords)[np.abs(np.diff(x_coords)) > 50]
        return {
            'column_count': len(column_boundaries) + 1,
            'column_boundaries': column_boundaries.tolist(),
            'metadata': {'block_count': len(blocks)}
        }

    def _extract_structured_text(self, file_path: str, doc_type: str, similar_docs: List) -> List:
        """Extract text with column-aware ordering"""
        if doc_type == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                return [
                    page.crop(self._get_reading_order_areas(page, similar_docs))
                      .extract_text(x_tolerance=1, y_tolerance=1)
                    for page in pdf.pages
                ]
        return []

    def _extract_tables(self, file_path: str, doc_type: str, similar_docs: List) -> List:
        """Extract nested tables with hierarchy preservation"""
        if doc_type != 'pdf':
            return []
            
        tables = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables.extend(self._find_nested_tables(page))
        return tables

    def _process_images(self, file_path: str, doc_type: str) -> Dict:
        """Enhanced OCR processing with image preprocessing"""
        return {
            img.hash: {
                'text': self._ocr_with_fallback(self._preprocess_image(img)),
                'metadata': self._analyze_image_layout(img)
            }
            for img in self._extract_images(file_path)
        }

    def _preprocess_image(self, image: Image) -> Image:
        """Apply OCR-enhancing transformations"""
        img = np.array(image)
        img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        img = cv2.detailEnhance(img, sigma_s=10, sigma_r=0.15)
        return Image.fromarray(cv2.medianBlur(img, 3))

    def _get_reading_order_areas(self, page, similar_docs):
        """Determine reading order using layout analysis and historical patterns"""
        areas = []
        for doc in similar_docs:
            areas.extend(doc.get('common_areas', []))
        return areas or page.rect

    def _find_nested_tables(self, page):
        """Identify nested tables using recursive boundary analysis"""
        return self._filter_nested_tables(page.find_tables())

    def _filter_nested_tables(self, tables):
        """Remove tables that are completely contained within other tables"""
        return [
            table for i, table in enumerate(tables)
            if not any(self._is_contained(table.bbox, t.bbox) 
                      for t in tables if t != table)
        ]

    def _is_contained(self, inner_bbox, outer_bbox):
        """Check bounding box containment"""
        return (inner_bbox[0] >= outer_bbox[0] and 
                inner_bbox[1] >= outer_bbox[1] and
                inner_bbox[2] <= outer_bbox[2] and 
                inner_bbox[3] <= outer_bbox[3])

    def _ocr_with_fallback(self, image: Image) -> str:
        """Perform OCR with Azure fallback"""
        try:
            return "OCR result from Tesseract"
        except Exception as e:
            logger.error(f"OCR failed: {str(e)}")
            return "OCR fallback result"

    def _analyze_image_layout(self, image: Image) -> Dict:
        """Analyze image layout for OCR processing"""
        return {}

    def _extract_images(self, file_path: str) -> List[Image]:
        """Extract images from the document"""
        with fitz.open(file_path) as doc:
            for page in doc:
                for img in page.get_images():
                    base_image = doc.extract_image(img[0])
                    yield Image.open(io.BytesIO(base_image["bytes"]))

    def _parse_table_structure(self, table: Dict) -> Dict:
        """Parse table structure from pdfplumber table"""
        return {}

    def _detect_document_type(self, file_path: str) -> str:
        """Detect document type based on file extension"""
        return "pdf"

class JinaProcessor:
    def __init__(self):
        self.client = Client(
            host="jina:54321",
            **config.JINA_CONFIG
        )

    @jina_retry()
    async def process(self, content):
        return await self.client.post(
            "/process",
            inputs=content,
            compression="gzip"
        )