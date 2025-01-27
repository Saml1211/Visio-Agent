from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class StepType(Enum):
    DOCUMENT_UPLOAD = "document_upload"
    FILE_PROCESSING = "file_processing"
    AI_ANALYSIS = "ai_analysis"
    VISIO_GENERATION = "visio_generation"
    DATA_EXPORT = "data_export"
    CUSTOM = "custom"

@dataclass
class WorkflowStep:
    id: str
    name: str
    type: StepType
    configuration: Dict[str, Any]
    input_mappings: Dict[str, str]
    output_mappings: Dict[str, str]
    error_handling: Dict
    retry_policy: Optional[Dict] = None
    timeout_seconds: Optional[int] = None

@dataclass
class WorkflowTransition:
    source_step: str
    target_step: str
    condition: Optional[str]
    transformation: Optional[Dict]

@dataclass
class Workflow:
    id: str
    name: str
    description: str
    version: str
    steps: List[WorkflowStep]
    transitions: List[WorkflowTransition]
    variables: Dict[str, Any]
    status: WorkflowStatus
    created_at: datetime
    modified_at: datetime

@dataclass
class DocumentProcessingWorkflow(Workflow):
    document_type: str
    extraction_settings: Dict
    validation_rules: List[Dict]

@dataclass
class VisioGenerationWorkflow(Workflow):
    template_id: str
    component_mappings: Dict
    layout_settings: Dict
    export_format: str

@dataclass
class WorkflowExecution:
    workflow: Workflow
    status: WorkflowStatus
    current_step: str
    variables: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime]
    logs: List[Dict]
    errors: List[Dict]

@dataclass
class WorkflowTemplate:
    id: str
    name: str
    description: str
    workflow_type: str
    default_configuration: Dict
    customization_options: Dict
    validation_schema: Dict 