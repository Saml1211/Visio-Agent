from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from src.models.document_models import ProcessedContent, AVComponent, VisioShape, VisioConnector
from src.services.service_interfaces import AIService

class RefinementType(Enum):
    DATA = "data"
    VISIO = "visio"

class RefinementStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class RefinementTask:
    id: str
    type: RefinementType
    input_data: Dict[str, Any]
    status: RefinementStatus
    iteration: int
    confidence_score: float
    issues: List[Dict]
    suggestions: List[Dict]
    metadata: Dict
    created_at: datetime
    updated_at: datetime

@dataclass
class LLMCapability:
    """Defines what a specific LLM is capable of handling"""
    name: str
    supported_tasks: List[RefinementType]
    specializations: List[str]  # e.g. ["technical_data", "layout_optimization"]
    max_input_size: int
    performance_metrics: Dict[str, float]
    cost_per_token: float

class RefinementOrchestrator:
    """Orchestrates the AI-driven refinement process"""
    
    def __init__(self, available_llms: List[LLMCapability], config: Dict):
        self.llms = available_llms
        self.config = config
        self.current_tasks: Dict[str, RefinementTask] = {}
    
    def select_llm(self, task: RefinementTask) -> LLMCapability:
        """Selects the most appropriate LLM for a given task based on capabilities and performance"""
        suitable_llms = [
            llm for llm in self.llms 
            if task.type in llm.supported_tasks
        ]
        
        if not suitable_llms:
            raise ValueError(f"No suitable LLM found for task type {task.type}")
        
        # Select based on specialization and performance metrics
        return max(suitable_llms, 
                  key=lambda llm: (
                      len(set(llm.specializations) & set(task.metadata.get("required_specializations", []))),
                      llm.performance_metrics.get("accuracy", 0),
                      -llm.cost_per_token
                  ))

    async def create_refinement_task(
        self,
        type: RefinementType,
        input_data: Dict[str, Any],
        metadata: Dict
    ) -> RefinementTask:
        """Creates a new refinement task"""
        task = RefinementTask(
            id=f"{type.value}_{datetime.now().timestamp()}",
            type=type,
            input_data=input_data,
            status=RefinementStatus.PENDING,
            iteration=0,
            confidence_score=0.0,
            issues=[],
            suggestions=[],
            metadata=metadata,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.current_tasks[task.id] = task
        return task

    async def execute_refinement_iteration(
        self,
        task: RefinementTask,
        llm_service: AIService
    ) -> Tuple[RefinementTask, bool]:
        """Executes one iteration of refinement"""
        task.status = RefinementStatus.IN_PROGRESS
        task.iteration += 1
        
        try:
            if task.type == RefinementType.DATA:
                result = await self._refine_data(task, llm_service)
            else:  # RefinementType.VISIO
                result = await self._refine_visio(task, llm_service)
            
            task.issues = result.get("issues", [])
            task.suggestions = result.get("suggestions", [])
            task.confidence_score = result.get("confidence_score", 0.0)
            task.status = RefinementStatus.COMPLETED
            
            # Determine if another iteration is needed
            needs_another_iteration = (
                task.iteration < self.config.get("max_iterations", 3) and
                (len(task.issues) > 0 or task.confidence_score < self.config.get("min_confidence", 0.95))
            )
            
            return task, needs_another_iteration
            
        except Exception as e:
            task.status = RefinementStatus.FAILED
            task.metadata["error"] = str(e)
            return task, False

    async def _refine_data(self, task: RefinementTask, llm_service: AIService) -> Dict:
        """Refines technical data using the selected LLM"""
        processed_content = task.input_data.get("processed_content")
        if not processed_content:
            raise ValueError("No processed content found in input data")
            
        # Analyze content using AI service
        analysis_result = await llm_service.analyze_content(processed_content)
        
        # Map relationships between entities
        entities = analysis_result.get("entities", [])
        relationships = await llm_service.map_relationships(entities)
        
        return {
            "issues": analysis_result.get("issues", []),
            "suggestions": analysis_result.get("suggestions", []),
            "confidence_score": analysis_result.get("confidence_score", 0.0),
            "refined_data": {
                "entities": entities,
                "relationships": relationships
            }
        }

    async def _refine_visio(self, task: RefinementTask, llm_service: AIService) -> Dict:
        """Refines Visio diagram layout using the selected LLM"""
        components = task.input_data.get("components", [])
        if not components:
            raise ValueError("No components found in input data")
            
        # Plan optimal layout
        layout_plan = await llm_service.plan_layout(components)
        
        return {
            "issues": layout_plan.get("issues", []),
            "suggestions": layout_plan.get("suggestions", []),
            "confidence_score": layout_plan.get("confidence_score", 0.0),
            "refined_layout": layout_plan.get("layout", {})
        }

class DataRefinementService:
    """Handles the AI-driven data refinement process"""
    
    def __init__(self, orchestrator: RefinementOrchestrator, llm_service: AIService):
        self.orchestrator = orchestrator
        self.llm_service = llm_service
    
    async def refine_technical_data(
        self,
        processed_content: ProcessedContent,
        metadata: Dict
    ) -> Tuple[ProcessedContent, List[Dict]]:
        """Refines technical data through multiple iterations"""
        
        task = await self.orchestrator.create_refinement_task(
            type=RefinementType.DATA,
            input_data={"processed_content": processed_content},
            metadata=metadata
        )
        
        refinement_history = []
        needs_iteration = True
        
        while needs_iteration:
            task, needs_iteration = await self.orchestrator.execute_refinement_iteration(
                task,
                self.llm_service
            )
            
            refinement_history.append({
                "iteration": task.iteration,
                "issues": task.issues,
                "suggestions": task.suggestions,
                "confidence_score": task.confidence_score,
                "timestamp": datetime.now()
            })
            
            if task.status == RefinementStatus.FAILED:
                break
        
        # Update processed content with refined data
        if task.status == RefinementStatus.COMPLETED:
            refined_data = task.input_data.get("refined_data", {})
            processed_content.structured_data.update(refined_data)
            processed_content.confidence_score = task.confidence_score
            
        return processed_content, refinement_history

class VisioRefinementService:
    """Handles the AI-driven Visio diagram refinement process"""
    
    def __init__(self, orchestrator: RefinementOrchestrator, llm_service: AIService):
        self.orchestrator = orchestrator
        self.llm_service = llm_service
    
    async def refine_visio_layout(
        self,
        components: List[AVComponent],
        metadata: Dict
    ) -> Tuple[Dict, List[Dict]]:
        """Refines Visio diagram layout through multiple iterations"""
        
        task = await self.orchestrator.create_refinement_task(
            type=RefinementType.VISIO,
            input_data={"components": components},
            metadata=metadata
        )
        
        refinement_history = []
        needs_iteration = True
        
        while needs_iteration:
            task, needs_iteration = await self.orchestrator.execute_refinement_iteration(
                task,
                self.llm_service
            )
            
            refinement_history.append({
                "iteration": task.iteration,
                "issues": task.issues,
                "suggestions": task.suggestions,
                "confidence_score": task.confidence_score,
                "timestamp": datetime.now()
            })
            
            if task.status == RefinementStatus.FAILED:
                break
        
        # Return the refined layout if successful
        final_layout = (
            task.input_data.get("refined_layout", {})
            if task.status == RefinementStatus.COMPLETED
            else {}
        )
        
        return final_layout, refinement_history 