import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

from .ai_service_config import AIServiceManager
from .rag_memory_service import RAGMemoryService
from .visio_generation_service import VisioGenerationService
from .self_learning_service import SelfLearningService

logger = logging.getLogger(__name__)

@dataclass
class WorkflowStep:
    """Represents a step in the workflow"""
    name: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class WorkflowResult:
    """Represents the result of a workflow execution"""
    workflow_id: str
    status: str
    steps: List[WorkflowStep]
    visio_file_path: Optional[str] = None
    pdf_file_path: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class RefinementOrchestrator:
    """Orchestrates the AI-powered refinement workflow"""
    
    def __init__(
        self,
        ai_service_manager: AIServiceManager,
        rag_memory: RAGMemoryService,
        visio_service: VisioGenerationService,
        self_learning_service: SelfLearningService,
        output_dir: Union[str, Path],
        max_refinement_iterations: int = 3,
        min_confidence_threshold: float = 0.8
    ):
        self.ai_service_manager = ai_service_manager
        self.rag_memory = rag_memory
        self.visio_service = visio_service
        self.self_learning_service = self_learning_service
        self.output_dir = Path(output_dir)
        self.max_refinement_iterations = max_refinement_iterations
        self.min_confidence_threshold = min_confidence_threshold
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Initialized refinement orchestrator")
    
    def process_document(
        self,
        document_path: Union[str, Path],
        template_name: str,
        workflow_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """Process a document through the complete workflow"""
        try:
            workflow_id = workflow_id or f"workflow_{datetime.utcnow().timestamp()}"
            steps: List[WorkflowStep] = []
            
            # Step 1: Data Extraction and Refinement
            data = self._refine_technical_data(
                document_path,
                workflow_id,
                additional_context,
                steps
            )
            
            # Step 2: Component Extraction
            components = self._extract_components(
                data,
                workflow_id,
                steps
            )
            
            # Step 3: Visio Layout Generation
            visio_result = self._generate_visio_layout(
                components,
                template_name,
                workflow_id,
                steps
            )
            
            # Create workflow record
            result = self._create_workflow_record(
                workflow_id,
                steps,
                visio_result,
                data
            )
            
            logger.info(f"Completed workflow: {workflow_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise
    
    def _refine_technical_data(
        self,
        document_path: Union[str, Path],
        workflow_id: str,
        additional_context: Optional[Dict[str, Any]],
        steps: List[WorkflowStep]
    ) -> Dict[str, Any]:
        """Refine technical data from document"""
        try:
            step = WorkflowStep(
                name="data_refinement",
                status="running",
                start_time=datetime.utcnow()
            )
            steps.append(step)
            
            # Get data refinement service
            service = self.ai_service_manager.get_provider("data_refinement")
            
            # Extract initial data
            with open(document_path, 'r') as f:
                content = f.read()
            
            # Get relevant knowledge from RAG
            knowledge = self.self_learning_service.retrieve_relevant_knowledge(
                context=content[:1000],  # Use first 1000 chars for context
                feedback_type="data_refinement"
            )
            # Initial analysis
            result = service.analyze_content(
                content=content,
                context={
                    "workflow_id": workflow_id,
                    "knowledge": knowledge
                }
                **additional_context if additional_context else {}
            )
            
            # Iterative refinement
            iteration = 0
            while iteration < self.max_refinement_iterations:
                confidence = result.get("confidence", 0.0)
                if confidence >= self.min_confidence_threshold:
                    break
                
                # Refine data
                result = service.analyze_content(
                    content=json.dumps(result),
                    context={
                        "workflow_id": workflow_id,
                        "iteration": iteration,
                        "previous_confidence": confidence,
                        "knowledge": knowledge
                    }
                )
                
                iteration += 1
            
            step.status = "completed"
            step.end_time = datetime.utcnow()
            step.metadata = {
                "iterations": iteration,
                "final_confidence": result.get("confidence", 0.0)
            }
            
            return result
            
        except Exception as e:
            step.status = "failed"
            step.end_time = datetime.utcnow()
            step.error = str(e)
            logger.error(f"Error refining technical data: {str(e)}")
            raise
    
    def _extract_components(
        self,
        data: Dict[str, Any],
        workflow_id: str,
        steps: List[WorkflowStep]
    ) -> List[Dict[str, Any]]:
        """Extract components from refined data"""
        try:
            step = WorkflowStep(
                name="component_extraction",
                status="running",
                start_time=datetime.utcnow()
            )
            steps.append(step)
            
            # Get component extraction service
            service = self.ai_service_manager.get_provider("component_extraction")
            
            # Get relevant knowledge
            knowledge = self.self_learning_service.retrieve_relevant_knowledge(
                context=json.dumps(data)[:1000],
                feedback_type="component_extraction"
            )
            
            # Extract components
            result = service.analyze_content(
                content=json.dumps(data),
                context={
                    "workflow_id": workflow_id,
                    "knowledge": knowledge
                }
            )
            
            # Validate components
            components = result.get("components", [])
            if not components:
                raise ValueError("No components extracted from data")
            
            step.status = "completed"
            step.end_time = datetime.utcnow()
            step.metadata = {
                "component_count": len(components),
                "confidence": result.get("confidence", 0.0)
            }
            
            return components
            
        except Exception as e:
            step.status = "failed"
            step.end_time = datetime.utcnow()
            step.error = str(e)
            logger.error(f"Error extracting components: {str(e)}")
            raise
    
    def _generate_visio_layout(
        self,
        components: List[Dict[str, Any]],
        template_name: str,
        workflow_id: str,
        steps: List[WorkflowStep]
    ) -> Dict[str, str]:
        """Generate Visio layout from components"""
        try:
            step = WorkflowStep(
                name="visio_generation",
                status="running",
                start_time=datetime.utcnow()
            )
            steps.append(step)
            
            # Get layout service
            service = self.ai_service_manager.get_provider("layout_generation")
            
            # Get relevant knowledge
            knowledge = self.self_learning_service.retrieve_relevant_knowledge(
                context=json.dumps(components)[:1000],
                feedback_type="layout_generation"
            )
            
            # Generate layout plan
            layout_plan = service.analyze_content(
                content=json.dumps(components),
                context={
                    "workflow_id": workflow_id,
                    "template_name": template_name,
                    "knowledge": knowledge
                }
            )
            
            # Generate Visio diagram
            visio_path = self.output_dir / f"{workflow_id}.vsdx"
            pdf_path = self.output_dir / f"{workflow_id}.pdf"
            
            self.visio_service.generate_diagram(
                template_name=template_name,
                components=components,
                layout_plan=layout_plan,
                output_path=visio_path,
                generate_pdf=True,
                pdf_path=pdf_path
            )
            
            step.status = "completed"
            step.end_time = datetime.utcnow()
            step.metadata = {
                "visio_path": str(visio_path),
                "pdf_path": str(pdf_path),
                "confidence": layout_plan.get("confidence", 0.0)
            }
            
            return {
                "visio_path": str(visio_path),
                "pdf_path": str(pdf_path)
            }
            
        except Exception as e:
            step.status = "failed"
            step.end_time = datetime.utcnow()
            step.error = str(e)
            logger.error(f"Error generating Visio layout: {str(e)}")
            raise
    
    def _create_workflow_record(
        self,
        workflow_id: str,
        steps: List[WorkflowStep],
        visio_result: Dict[str, str],
        raw_data: Dict[str, Any]
    ) -> WorkflowResult:
        """Create workflow record with results"""
        try:
            # Calculate overall status
            failed_steps = [s for s in steps if s.status == "failed"]
            status = "failed" if failed_steps else "completed"
            
            # Create workflow result
            result = WorkflowResult(
                workflow_id=workflow_id,
                status=status,
                steps=steps,
                visio_file_path=visio_result.get("visio_path"),
                pdf_file_path=visio_result.get("pdf_path"),
                raw_data=raw_data,
                metadata={
                    "created_at": datetime.utcnow().isoformat(),
                    "step_count": len(steps),
                    "failed_steps": len(failed_steps)
                }
            )
            
            # Store in RAG memory
            self.rag_memory.store_entry(
                content=json.dumps({
                    "workflow_id": workflow_id,
                    "status": status,
                    "steps": [
                        {
                            "name": s.name,
                            "status": s.status,
                            "duration": (s.end_time - s.start_time).total_seconds()
                            if s.end_time and s.start_time else None,
                            "error": s.error,
                            "metadata": s.metadata
                        }
                        for s in steps
                    ],
                    "raw_data": raw_data
                }),
                metadata={
                    "type": "workflow_record",
                    "workflow_id": workflow_id,
                    "status": status,
                    "created_at": result.metadata["created_at"]
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating workflow record: {str(e)}")
            raise 