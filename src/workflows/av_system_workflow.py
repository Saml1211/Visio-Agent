import logging
from typing import Dict, List, Optional
from datetime import datetime

from src.models.document_models import Document, ProcessedContent, AVComponent
from src.models.workflow_definitions import (
    Workflow, WorkflowStep, WorkflowTransition,
    WorkflowStatus, StepType
)
from src.services.ai_refinement_service import (
    RefinementOrchestrator,
    DataRefinementService,
    VisioRefinementService,
    RefinementType
)
from src.services.llm_ai_service import LLMBasedAIService
from config.ai_refinement_config import AVAILABLE_LLMS, REFINEMENT_CONFIG

logger = logging.getLogger(__name__)

class AVSystemWorkflow:
    """Example workflow for processing AV system documents"""
    
    def __init__(
        self,
        api_key: str,
        storage_path: str,
        config: Optional[Dict] = None
    ):
        self.config = config or REFINEMENT_CONFIG
        
        # Initialize services
        self.ai_service = LLMBasedAIService(api_key=api_key)
        self.orchestrator = RefinementOrchestrator(
            available_llms=AVAILABLE_LLMS,
            config=self.config
        )
        self.data_refinement = DataRefinementService(
            orchestrator=self.orchestrator,
            llm_service=self.ai_service
        )
        self.visio_refinement = VisioRefinementService(
            orchestrator=self.orchestrator,
            llm_service=self.ai_service
        )
        
        self.storage_path = storage_path
    
    async def process_document(self, document: Document) -> Dict:
        """Process a single AV system document"""
        try:
            logger.info(f"Starting document processing workflow for {document.id}")
            
            # Step 1: Initial data extraction and refinement
            processed_content, data_history = await self._refine_technical_data(document)
            
            # Step 2: Extract AV components
            components = await self._extract_components(processed_content)
            
            # Step 3: Generate and refine Visio layout
            layout, layout_history = await self._generate_visio_layout(components)
            
            # Step 4: Create workflow record
            workflow = self._create_workflow_record(
                document,
                processed_content,
                components,
                layout,
                data_history,
                layout_history
            )
            
            logger.info(f"Completed document processing workflow for {document.id}")
            
            return {
                "workflow": workflow,
                "processed_content": processed_content,
                "components": components,
                "layout": layout,
                "data_history": data_history,
                "layout_history": layout_history
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {str(e)}")
            raise
    
    async def _refine_technical_data(
        self,
        document: Document
    ) -> tuple[ProcessedContent, List[Dict]]:
        """Refine technical data from document"""
        try:
            logger.info(f"Starting technical data refinement for {document.id}")
            
            metadata = {
                "document_id": document.id,
                "document_type": document.metadata.file_type.value,
                "required_specializations": ["technical_data", "av_systems"]
            }
            
            processed_content = document.content or ProcessedContent(
                raw_text="",
                structured_data={},
                extracted_entities=[],
                confidence_score=0.0,
                processing_metadata={}
            )
            
            refined_content, history = await self.data_refinement.refine_technical_data(
                processed_content,
                metadata
            )
            
            logger.info(f"Completed technical data refinement for {document.id}")
            return refined_content, history
            
        except Exception as e:
            logger.error(f"Error refining technical data: {str(e)}")
            raise
    
    async def _extract_components(self, content: ProcessedContent) -> List[AVComponent]:
        """Extract AV components from processed content"""
        try:
            logger.info("Extracting AV components from processed content")
            
            # This is a placeholder implementation
            # In a real system, this would parse the structured data and create AVComponent objects
            components = []
            
            for entity in content.structured_data.get("entities", []):
                if isinstance(entity, dict) and entity.get("type") in ["projector", "screen", "audio"]:
                    component = AVComponent(
                        id=f"{entity['type']}_{len(components)}",
                        name=entity.get("name", ""),
                        type=entity["type"],
                        manufacturer=entity.get("manufacturer", ""),
                        model=entity.get("model", ""),
                        specifications=entity.get("specifications", {}),
                        connections=entity.get("connections", []),
                        position={"x": 0, "y": 0},  # Initial position
                        attributes=entity.get("attributes", {})
                    )
                    components.append(component)
            
            logger.info(f"Extracted {len(components)} components")
            return components
            
        except Exception as e:
            logger.error(f"Error extracting components: {str(e)}")
            raise
    
    async def _generate_visio_layout(
        self,
        components: List[AVComponent]
    ) -> tuple[Dict, List[Dict]]:
        """Generate and refine Visio layout"""
        try:
            logger.info(f"Starting Visio layout generation for {len(components)} components")
            
            metadata = {
                "required_specializations": ["layout_optimization", "visual_design"],
                "component_count": len(components),
                "layout_rules": self.config["visio_refinement"]["layout_rules"]
            }
            
            layout, history = await self.visio_refinement.refine_visio_layout(
                components,
                metadata
            )
            
            logger.info("Completed Visio layout generation")
            return layout, history
            
        except Exception as e:
            logger.error(f"Error generating Visio layout: {str(e)}")
            raise
    
    def _create_workflow_record(
        self,
        document: Document,
        processed_content: ProcessedContent,
        components: List[AVComponent],
        layout: Dict,
        data_history: List[Dict],
        layout_history: List[Dict]
    ) -> Workflow:
        """Create a workflow record for tracking"""
        
        # Create workflow steps
        steps = [
            WorkflowStep(
                id="data_extraction",
                name="Technical Data Extraction",
                type=StepType.FILE_PROCESSING,
                configuration={},
                input_mappings={"document": document.id},
                output_mappings={"content": "processed_content"},
                error_handling={"retry_count": 3}
            ),
            WorkflowStep(
                id="data_refinement",
                name="Data Refinement",
                type=StepType.AI_ANALYSIS,
                configuration={"history": data_history},
                input_mappings={"content": "processed_content"},
                output_mappings={"refined_content": "refined_content"},
                error_handling={"retry_count": 3}
            ),
            WorkflowStep(
                id="visio_generation",
                name="Visio Layout Generation",
                type=StepType.VISIO_GENERATION,
                configuration={"history": layout_history},
                input_mappings={"components": "components"},
                output_mappings={"layout": "layout"},
                error_handling={"retry_count": 3}
            )
        ]
        
        # Create workflow transitions
        transitions = [
            WorkflowTransition(
                source_step="data_extraction",
                target_step="data_refinement",
                condition="success",
                transformation=None
            ),
            WorkflowTransition(
                source_step="data_refinement",
                target_step="visio_generation",
                condition="success",
                transformation=None
            )
        ]
        
        # Create workflow record
        workflow = Workflow(
            id=f"workflow_{document.id}",
            name=f"AV System Processing - {document.metadata.file_name}",
            description="Processing workflow for AV system document",
            version="1.0",
            steps=steps,
            transitions=transitions,
            variables={
                "document_id": document.id,
                "storage_path": self.storage_path
            },
            status=WorkflowStatus.COMPLETED,
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
        
        return workflow 