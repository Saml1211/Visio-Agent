from langgraph.graph import StateGraph
from langgraph.checkpoint import VisioCheckpointer
from .workflow_orchestrator import RefinementOrchestrator, create_visio_workflow

class HybridOrchestrationEngine:
    def __init__(self):
        self.checkpointer = VisioCheckpointer()
        self.langgraph_flow = create_visio_workflow().with_config(
            {"checkpointer": self.checkpointer}
        )
        self.legacy_orchestrator = RefinementOrchestrator(
            ai_service_manager=AIServiceManager(),
            rag_memory=RAGMemoryService(),
            visio_service=VisioGenerationService(),
            self_learning_service=SelfLearningService()
        )
        
    async def process_request(self, input_data: dict):
        """Hybrid processing with automatic fallback"""
        try:
            # Try LangGraph first with state preservation
            workflow_id = input_data.get("workflow_id") or self._generate_workflow_id()
            
            async for step in self.langgraph_flow.astream(
                input_data,
                {"configurable": {"thread_id": workflow_id}}
            ):
                yield step
                # Persist state after each step
                await self.checkpointer.save_state(workflow_id, step)
                
        except LangGraphError as e:
            logger.warning(f"LangGraph failed, falling back: {str(e)}")
            try:
                # Convert to legacy format
                legacy_result = await self.legacy_orchestrator.process_document(
                    document_path=input_data["document_path"],
                    template_name=input_data["template"],
                    additional_context=input_data.get("context")
                )
                yield self._convert_legacy_result(legacy_result)
            except Exception as legacy_error:
                raise OrchestrationError(
                    f"Hybrid orchestration failed: {str(legacy_error)}"
                )

    def _generate_workflow_id(self) -> str:
        return f"wf_{datetime.now().timestamp()}_{uuid.uuid4().hex[:6]}"
    
    def _convert_legacy_result(self, result: WorkflowResult) -> dict:
        return {
            "workflow_id": result.workflow_id,
            "status": result.status,
            "steps": [s.name for s in result.steps],
            "artifacts": {
                "visio": result.visio_file_path,
                "pdf": result.pdf_file_path
            }
        } 