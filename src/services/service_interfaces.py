from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from src.models.document_models import Document, ProcessedContent, AVComponent, VisioShape, VisioConnector
from src.models.workflow_definitions import Workflow, WorkflowExecution

class DocumentProcessingService(ABC):
    @abstractmethod
    async def process_document(self, document: Document) -> ProcessedContent:
        pass

    @abstractmethod
    async def extract_entities(self, content: ProcessedContent) -> List[Dict]:
        pass

    @abstractmethod
    async def validate_content(self, content: ProcessedContent) -> bool:
        pass

class AIService(ABC):
    @abstractmethod
    async def analyze_content(self, content: ProcessedContent) -> Dict:
        pass

    @abstractmethod
    async def map_relationships(self, entities: List[Dict]) -> List[Dict]:
        pass

    @abstractmethod
    async def plan_layout(self, components: List[AVComponent]) -> Dict:
        pass

class VisioService(ABC):
    @abstractmethod
    async def create_diagram(self, components: List[AVComponent], layout: Dict) -> str:
        pass

    @abstractmethod
    async def place_shapes(self, components: List[AVComponent]) -> List[VisioShape]:
        pass

    @abstractmethod
    async def create_connections(self, components: List[AVComponent]) -> List[VisioConnector]:
        pass

    @abstractmethod
    async def export_to_pdf(self, diagram_path: str) -> str:
        pass

class StorageService(ABC):
    @abstractmethod
    async def save_document(self, document: Document) -> str:
        pass

    @abstractmethod
    async def load_document(self, document_id: str) -> Document:
        pass

    @abstractmethod
    async def list_documents(self, filters: Optional[Dict] = None) -> List[Document]:
        pass

class WorkflowService(ABC):
    @abstractmethod
    async def create_workflow(self, template_id: str, configuration: Dict) -> Workflow:
        pass

    @abstractmethod
    async def execute_workflow(self, workflow: Workflow) -> WorkflowExecution:
        pass

    @abstractmethod
    async def get_workflow_status(self, execution_id: str) -> Dict:
        pass

class LoggingService(ABC):
    @abstractmethod
    def log_event(self, event_type: str, details: Dict) -> None:
        pass

    @abstractmethod
    def log_error(self, error: Exception, context: Dict) -> None:
        pass

    @abstractmethod
    def get_logs(self, filters: Optional[Dict] = None) -> List[Dict]:
        pass 