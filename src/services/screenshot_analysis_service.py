from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import logging
import json
import cv2
import numpy as np
from PIL import Image, ImageFont
import pytesseract
from sklearn.cluster import KMeans
import imagehash
from io import BytesIO
import base64
from .exceptions import AnalysisError
from .rag_memory_service import RAGMemoryService

logger = logging.getLogger(__name__)

@dataclass
class ColorPalette:
    """Color palette extracted from image"""
    primary_colors: List[Tuple[int, int, int]]  # RGB values
    secondary_colors: List[Tuple[int, int, int]]
    background_color: Tuple[int, int, int]
    accent_colors: List[Tuple[int, int, int]]
    color_distribution: Dict[Tuple[int, int, int], float]

@dataclass
class FontInfo:
    """Font information extracted from image"""
    font_sizes: List[int]
    font_families: List[str]
    text_colors: List[Tuple[int, int, int]]
    heading_fonts: List[str]
    body_fonts: List[str]
    is_serif: bool
    confidence: float

@dataclass
class LogoDetection:
    """Logo detection result"""
    bounding_box: Tuple[int, int, int, int]  # x, y, width, height
    confidence: float
    logo_type: Optional[str] = None
    matched_template: Optional[str] = None
    description: Optional[str] = None

@dataclass
class VisualAnalysisResult:
    """Complete visual analysis result"""
    image_hash: str
    color_palette: ColorPalette
    font_info: FontInfo
    detected_logos: List[LogoDetection]
    symbols: List[Dict[str, Any]]
    layout_info: Dict[str, Any]
    processing_time_ms: float

class ScreenshotAnalysisService:
    """Service for analyzing screenshots with enhanced visual understanding"""
    
    def __init__(
        self,
        rag_memory: RAGMemoryService,
        logo_templates_dir: Optional[Path] = None,
        enable_gpu: bool = False
    ):
        """Initialize the screenshot analysis service
        
        Args:
            rag_memory: RAG memory service for caching results
            logo_templates_dir: Directory containing logo templates
            enable_gpu: Whether to enable GPU acceleration
        """
        self.rag_memory = rag_memory
        self.logo_templates_dir = Path(logo_templates_dir) if logo_templates_dir else None
        self.enable_gpu = enable_gpu
        
        # Load logo templates if available
        self.logo_templates = {}
        if self.logo_templates_dir and self.logo_templates_dir.exists():
            self._load_logo_templates()
        
        # Initialize models
        self._init_models()
        
        logger.info(
            f"Initialized ScreenshotAnalysisService with "
            f"{len(self.logo_templates)} logo templates"
        )
    
    def _init_models(self) -> None:
        """Initialize computer vision models"""
        try:
            # Initialize OpenCV DNN for logo detection
            self.logo_detector = cv2.dnn.readNet(
                "models/yolov4-tiny.weights",
                "models/yolov4-tiny.cfg"
            )
            if self.enable_gpu:
                self.logo_detector.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.logo_detector.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            
            # Initialize OCR
            self.ocr_config = "--psm 11"  # Sparse text mode
            
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            raise AnalysisError(f"Failed to initialize models: {str(e)}")
    
    def _load_logo_templates(self) -> None:
        """Load logo template images"""
        try:
            for template_path in self.logo_templates_dir.glob("*.png"):
                template = cv2.imread(str(template_path))
                if template is not None:
                    self.logo_templates[template_path.stem] = template
                    
        except Exception as e:
            logger.error(f"Error loading logo templates: {str(e)}")
            raise AnalysisError(f"Failed to load logo templates: {str(e)}")
    
    async def analyze_screenshot(
        self,
        image_path: Path,
        use_cache: bool = True
    ) -> VisualAnalysisResult:
        """Analyze a screenshot for visual elements
        
        Args:
            image_path: Path to screenshot image
            use_cache: Whether to use cached results
            
        Returns:
            VisualAnalysisResult containing analysis data
        """
        try:
            # Calculate image hash
            with Image.open(image_path) as img:
                image_hash = str(imagehash.average_hash(img))
            
            # Check cache
            if use_cache:
                cache_key = f"screenshot_analysis_{image_hash}"
                if cached := await self.rag_memory.query_memory(cache_key):
                    logger.info(f"Found cached analysis for {image_path}")
                    return VisualAnalysisResult(**cached[0].content)
            
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise AnalysisError(f"Failed to load image: {image_path}")
            
            # Perform analysis
            color_palette = self._extract_color_palette(image)
            font_info = self._extract_font_info(image)
            detected_logos = self._detect_logos(image)
            symbols = self._detect_symbols(image)
            layout_info = self._analyze_layout(image)
            
            # Create result
            result = VisualAnalysisResult(
                image_hash=image_hash,
                color_palette=color_palette,
                font_info=font_info,
                detected_logos=detected_logos,
                symbols=symbols,
                layout_info=layout_info,
                processing_time_ms=0.0  # Updated later
            )
            
            # Cache result
            await self.rag_memory.store_entry(
                content=result.__dict__,
                metadata={
                    'type': 'screenshot_analysis',
                    'image_hash': image_hash,
                    'cache_key': f"screenshot_analysis_{image_hash}"
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing screenshot {image_path}: {str(e)}")
            raise AnalysisError(f"Screenshot analysis failed: {str(e)}")
    
    def _extract_color_palette(self, image: np.ndarray) -> ColorPalette:
        """Extract color palette from image
        
        Args:
            image: OpenCV image array
            
        Returns:
            ColorPalette containing color information
        """
        try:
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Reshape image for clustering
            pixels = image_rgb.reshape(-1, 3)
            
            # Cluster colors
            kmeans = KMeans(n_clusters=8, n_init=10)
            kmeans.fit(pixels)
            
            # Get color counts
            unique, counts = np.unique(
                kmeans.labels_,
                return_counts=True
            )
            
            # Sort colors by frequency
            colors = [(
                int(color[0]),
                int(color[1]),
                int(color[2])
            ) for color in kmeans.cluster_centers_]
            
            color_counts = dict(zip(colors, counts))
            total_pixels = sum(counts)
            
            # Calculate distribution
            distribution = {
                color: count / total_pixels
                for color, count in color_counts.items()
            }
            
            # Sort colors by frequency
            sorted_colors = sorted(
                colors,
                key=lambda x: color_counts[x],
                reverse=True
            )
            
            return ColorPalette(
                primary_colors=sorted_colors[:2],
                secondary_colors=sorted_colors[2:4],
                background_color=sorted_colors[0],  # Most common color
                accent_colors=sorted_colors[4:6],
                color_distribution=distribution
            )
            
        except Exception as e:
            logger.error(f"Error extracting color palette: {str(e)}")
            raise AnalysisError(f"Color palette extraction failed: {str(e)}")
    
    def _extract_font_info(self, image: np.ndarray) -> FontInfo:
        """Extract font information from image
        
        Args:
            image: OpenCV image array
            
        Returns:
            FontInfo containing font information
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # OCR with detailed output
            ocr_data = pytesseract.image_to_data(
                gray,
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract font sizes
            font_sizes = []
            for height in ocr_data['height']:
                if height > 0:
                    font_sizes.append(int(height * 0.75))  # Approximate
            
            # Analyze text colors
            text_colors = []
            for i, (x, y, w, h) in enumerate(zip(
                ocr_data['left'],
                ocr_data['top'],
                ocr_data['width'],
                ocr_data['height']
            )):
                if w > 0 and h > 0:
                    roi = image[y:y+h, x:x+w]
                    avg_color = cv2.mean(roi)[:3]
                    text_colors.append((
                        int(avg_color[2]),
                        int(avg_color[1]),
                        int(avg_color[0])
                    ))
            
            # Estimate font families
            is_serif = self._estimate_serif_presence(gray)
            
            # Group fonts by size
            sizes = sorted(set(font_sizes))
            heading_sizes = sizes[-2:] if len(sizes) > 2 else sizes
            body_sizes = sizes[:-2] if len(sizes) > 2 else sizes
            
            return FontInfo(
                font_sizes=sorted(set(font_sizes)),
                font_families=['serif'] if is_serif else ['sans-serif'],
                text_colors=list(set(text_colors)),
                heading_fonts=['serif'] if is_serif else ['sans-serif'],
                body_fonts=['serif'] if is_serif else ['sans-serif'],
                is_serif=is_serif,
                confidence=0.8 if font_sizes else 0.0
            )
            
        except Exception as e:
            logger.error(f"Error extracting font info: {str(e)}")
            raise AnalysisError(f"Font info extraction failed: {str(e)}")
    
    def _detect_logos(self, image: np.ndarray) -> List[LogoDetection]:
        """Detect logos in image
        
        Args:
            image: OpenCV image array
            
        Returns:
            List of LogoDetection results
        """
        try:
            detected_logos = []
            
            # Template matching for known logos
            if self.logo_templates:
                for name, template in self.logo_templates.items():
                    result = cv2.matchTemplate(
                        image,
                        template,
                        cv2.TM_CCOEFF_NORMED
                    )
                    threshold = 0.8
                    locations = np.where(result >= threshold)
                    
                    for pt in zip(*locations[::-1]):
                        detected_logos.append(LogoDetection(
                            bounding_box=(
                                pt[0],
                                pt[1],
                                template.shape[1],
                                template.shape[0]
                            ),
                            confidence=float(result[pt[1], pt[0]]),
                            logo_type=name,
                            matched_template=name
                        ))
            
            # Generic logo detection using YOLOv4
            blob = cv2.dnn.blobFromImage(
                image,
                1/255.0,
                (416, 416),
                swapRB=True,
                crop=False
            )
            self.logo_detector.setInput(blob)
            detections = self.logo_detector.forward()
            
            for detection in detections:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                
                if confidence > 0.5:  # Confidence threshold
                    center_x = int(detection[0] * image.shape[1])
                    center_y = int(detection[1] * image.shape[0])
                    width = int(detection[2] * image.shape[1])
                    height = int(detection[3] * image.shape[0])
                    
                    x = int(center_x - width/2)
                    y = int(center_y - height/2)
                    
                    detected_logos.append(LogoDetection(
                        bounding_box=(x, y, width, height),
                        confidence=float(confidence),
                        logo_type="generic",
                        description="Generic logo detected"
                    ))
            
            return detected_logos
            
        except Exception as e:
            logger.error(f"Error detecting logos: {str(e)}")
            raise AnalysisError(f"Logo detection failed: {str(e)}")
    
    def _detect_symbols(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect symbols and icons in image
        
        Args:
            image: OpenCV image array
            
        Returns:
            List of detected symbols with metadata
        """
        try:
            symbols = []
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(
                edges,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            for contour in contours:
                # Filter small contours
                if cv2.contourArea(contour) < 100:
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio
                aspect_ratio = float(w)/h
                if 0.8 <= aspect_ratio <= 1.2:  # Nearly square
                    roi = image[y:y+h, x:x+w]
                    
                    symbols.append({
                        'bounding_box': (x, y, w, h),
                        'area': cv2.contourArea(contour),
                        'aspect_ratio': aspect_ratio,
                        'is_filled': self._check_fill(roi),
                        'symmetry_score': self._calculate_symmetry(roi)
                    })
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error detecting symbols: {str(e)}")
            raise AnalysisError(f"Symbol detection failed: {str(e)}")
    
    def _analyze_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """Analyze image layout
        
        Args:
            image: OpenCV image array
            
        Returns:
            Dict containing layout information
        """
        try:
            height, width = image.shape[:2]
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find lines
            lines = cv2.HoughLinesP(
                edges,
                1,
                np.pi/180,
                threshold=100,
                minLineLength=100,
                maxLineGap=10
            )
            
            horizontal_lines = []
            vertical_lines = []
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.abs(np.arctan2(y2-y1, x2-x1) * 180.0 / np.pi)
                    
                    if angle < 10 or angle > 170:
                        horizontal_lines.append((x1, y1, x2, y2))
                    elif 80 < angle < 100:
                        vertical_lines.append((x1, y1, x2, y2))
            
            return {
                'image_size': (width, height),
                'aspect_ratio': width / height,
                'horizontal_lines': len(horizontal_lines),
                'vertical_lines': len(vertical_lines),
                'grid_score': self._calculate_grid_score(
                    horizontal_lines,
                    vertical_lines,
                    width,
                    height
                ),
                'symmetry': self._check_layout_symmetry(gray)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing layout: {str(e)}")
            raise AnalysisError(f"Layout analysis failed: {str(e)}")
    
    def _estimate_serif_presence(self, gray_image: np.ndarray) -> bool:
        """Estimate if text uses serif fonts
        
        Args:
            gray_image: Grayscale image array
            
        Returns:
            Boolean indicating serif presence
        """
        try:
            # Edge detection
            edges = cv2.Canny(gray_image, 50, 150)
            
            # Count small horizontal lines near text
            text_data = pytesseract.image_to_data(
                gray_image,
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            serif_score = 0
            total_chars = 0
            
            for i, (x, y, w, h) in enumerate(zip(
                text_data['left'],
                text_data['top'],
                text_data['width'],
                text_data['height']
            )):
                if w > 0 and h > 0:
                    # Check edges near character boundaries
                    roi = edges[y:y+h, x:x+w]
                    horizontal_lines = cv2.HoughLinesP(
                        roi,
                        1,
                        np.pi/180,
                        threshold=10,
                        minLineLength=3,
                        maxLineGap=2
                    )
                    
                    if horizontal_lines is not None:
                        serif_score += len(horizontal_lines)
                    total_chars += 1
            
            return (serif_score / total_chars) > 2 if total_chars > 0 else False
            
        except Exception:
            return False
    
    def _check_fill(self, roi: np.ndarray) -> bool:
        """Check if region is filled
        
        Args:
            roi: Region of interest array
            
        Returns:
            Boolean indicating if region is filled
        """
        try:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(
                gray,
                127,
                255,
                cv2.THRESH_BINARY
            )
            return np.mean(binary) < 127
            
        except Exception:
            return False
    
    def _calculate_symmetry(self, roi: np.ndarray) -> float:
        """Calculate symmetry score for region
        
        Args:
            roi: Region of interest array
            
        Returns:
            Symmetry score between 0 and 1
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Get dimensions
            height, width = gray.shape
            
            # Calculate horizontal symmetry
            left = gray[:, :width//2]
            right = cv2.flip(gray[:, width//2:], 1)
            h_diff = np.mean(np.abs(left - right))
            
            # Calculate vertical symmetry
            top = gray[:height//2, :]
            bottom = cv2.flip(gray[height//2:, :], 0)
            v_diff = np.mean(np.abs(top - bottom))
            
            # Combine scores
            symmetry = 1.0 - (h_diff + v_diff) / 510  # Max diff is 255 * 2
            return max(0.0, min(1.0, symmetry))
            
        except Exception:
            return 0.0
    
    def _calculate_grid_score(
        self,
        horizontal_lines: List[Tuple[int, int, int, int]],
        vertical_lines: List[Tuple[int, int, int, int]],
        width: int,
        height: int
    ) -> float:
        """Calculate grid-like layout score
        
        Args:
            horizontal_lines: List of horizontal line coordinates
            vertical_lines: List of vertical line coordinates
            width: Image width
            height: Image height
            
        Returns:
            Grid score between 0 and 1
        """
        try:
            if not horizontal_lines or not vertical_lines:
                return 0.0
            
            # Calculate line spacing consistency
            h_spacing = []
            for i in range(1, len(horizontal_lines)):
                h_spacing.append(
                    horizontal_lines[i][1] - horizontal_lines[i-1][1]
                )
            
            v_spacing = []
            for i in range(1, len(vertical_lines)):
                v_spacing.append(
                    vertical_lines[i][0] - vertical_lines[i-1][0]
                )
            
            # Calculate variance in spacing
            h_variance = np.var(h_spacing) if h_spacing else float('inf')
            v_variance = np.var(v_spacing) if v_spacing else float('inf')
            
            # Calculate coverage
            h_coverage = len(horizontal_lines) * np.mean(h_spacing) / height if h_spacing else 0
            v_coverage = len(vertical_lines) * np.mean(v_spacing) / width if v_spacing else 0
            
            # Combine metrics
            spacing_score = 1.0 / (1.0 + h_variance + v_variance)
            coverage_score = (h_coverage + v_coverage) / 2
            
            return spacing_score * coverage_score
            
        except Exception:
            return 0.0
    
    def _check_layout_symmetry(self, gray_image: np.ndarray) -> float:
        """Check layout symmetry
        
        Args:
            gray_image: Grayscale image array
            
        Returns:
            Symmetry score between 0 and 1
        """
        try:
            height, width = gray_image.shape
            
            # Calculate horizontal symmetry
            left = gray_image[:, :width//2]
            right = cv2.flip(gray_image[:, width//2:], 1)
            h_symmetry = 1.0 - np.mean(np.abs(left - right)) / 255
            
            # Calculate vertical symmetry
            top = gray_image[:height//2, :]
            bottom = cv2.flip(gray_image[height//2:, :], 0)
            v_symmetry = 1.0 - np.mean(np.abs(top - bottom)) / 255
            
            return (h_symmetry + v_symmetry) / 2
            
        except Exception:
            return 0.0

# Limitations:
# 1. Basic logo detection without deep learning model
# 2. Limited font family detection
# 3. Simple color clustering without semantic meaning
# 4. No text style analysis (bold, italic, etc.)
# 5. Basic symbol detection without classification
# 6. Limited layout analysis capabilities
# 7. No support for transparent backgrounds
# 8. No animation or dynamic content analysis 