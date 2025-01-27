from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime

class DocumentType(Enum):
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DocumentMetadata:
    file_name: str
    file_type: DocumentType
    file_size: int
    upload_date: datetime
    last_modified: datetime
    mime_type: str
    checksum: str

@dataclass
class ProcessedContent:
    raw_text: str
    structured_data: Dict
    extracted_entities: List[Dict]
    confidence_score: float
    processing_metadata: Dict

@dataclass
class Document:
    id: str
    metadata: DocumentMetadata
    status: ProcessingStatus
    content: Optional[ProcessedContent] = None
    error_message: Optional[str] = None

@dataclass
class AVComponent:
    id: str
    name: str
    type: str
    manufacturer: str
    model: str
    specifications: Dict
    connections: List[Dict]
    position: Dict[str, float]  # x, y coordinates for Visio
    attributes: Dict  # Additional component-specific attributes

@dataclass
class VisioShape:
    component: AVComponent
    shape_type: str
    stencil_id: str
    position: Dict[str, float]
    size: Dict[str, float]
    style: Dict
    text_properties: Dict

@dataclass
class VisioConnector:
    source_component: str
    target_component: str
    connector_type: str
    routing: List[Dict[str, float]]
    label: Optional[str]
    style: Dict 