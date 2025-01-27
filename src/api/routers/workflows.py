from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import logging
from ...services.service_registry import ServiceRegistry
from ...services.execution_engine import ExecutionEngine

logger = logging.getLogger(__name__)

class WorkflowStep(BaseModel):
    service_name: str = Field(..., description="Name of the service to execute")
    input_map: Dict[str, str] = Field(..., description="Mapping of service inputs to context keys")
    output_key: str = Field(..., description="Key to store the service output in context")

class WorkflowRequest(BaseModel):
    steps: List[WorkflowStep]
    initial_data: Dict[str, Any]

router = APIRouter()

@router.post("/execute-workflow", status_code=status.HTTP_200_OK)
async def execute_workflow(request: WorkflowRequest):
    try:
        context = request.initial_data.copy()
        engine = ExecutionEngine()
        
        for step in request.steps:
            try:
                service = ServiceRegistry().get(step.service_name)
                if not service:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Service not found: {step.service_name}"
                    )
                    
                input_data = {k: context.get(v) for k, v in step.input_map.items()}
                if None in input_data.values():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required input for service: {step.service_name}"
                    )
                    
                result = await engine.run_service(step.service_name, input_data)
                context[step.output_key] = result
                
            except Exception as step_error:
                logger.error(f"Step execution failed: {str(step_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Step execution failed: {str(step_error)}"
                )
                
        return {"status": "success", "result": context}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        ) 