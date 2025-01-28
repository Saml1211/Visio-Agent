from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import logging
import tempfile
import shutil
from datetime import datetime
import aiofiles
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
import backoff
import asyncio
from enum import Enum

from ..services.workflow_orchestrator import RefinementOrchestrator, WorkflowResult
from ..services.ai_service_config import AIServiceManager
from ..services.rag_memory_service import RAGMemoryService
from ..services.visio_generation_service import VisioGenerationService
from ..services.self_learning_service import SelfLearningService
from src.services.visio_check import verify_visio_installation
from src.services.workflow_verifier import WorkflowVerifier

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LLD Automation System",
    description="AI-powered Low Level Design automation system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create temp directory for uploads
UPLOAD_DIR = Path("temp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize services
ai_service_manager = AIServiceManager()
rag_memory = RAGMemoryService(
    memory_path="data/memory",
    embedding_model="text-embedding-ada-002"
)
visio_service = VisioGenerationService(
    templates_dir="data/templates",
    stencils_dir="data/stencils"
)
self_learning_service = SelfLearningService(
    ai_service_manager=ai_service_manager,
    rag_memory=rag_memory
)
orchestrator = RefinementOrchestrator(
    ai_service_manager=ai_service_manager,
    rag_memory=rag_memory,
    visio_service=visio_service,
    self_learning_service=self_learning_service,
    output_dir="data/output"
)

# Initialize Redis for rate limiting
redis_client = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(redis_client)
    
    # Critical system verification
    verify_visio_installation()
    
    # Component workflow validation
    verifier = WorkflowVerifier()
    results = verifier.verify()
    
    if any("✗" in result for component in results.values() for result in component):
        raise RuntimeError("System verification failed - check component status")

class ProcessRequest(BaseModel):
    """Request model for document processing"""
    template_name: str
    additional_context: Optional[Dict[str, Any]] = None

class FeedbackRequest(BaseModel):
    """Request model for user feedback"""
    workflow_id: str
    feedback_type: str
    input_data: Any
    expected_output: Any
    actual_output: Any
    user_feedback: str
    confidence_score: float

class FileType(str, Enum):
    VISIO = "visio"
    PDF = "pdf"

@backoff.on_exception(
    backoff.expo,
    (IOError, OSError),
    max_tries=3,
    max_time=30
)
async def cleanup_uploaded_file(file_path: str) -> None:
    """Clean up uploaded file after processing with retry logic"""
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            try:
                path.unlink()
                logger.info(f"Cleaned up file: {file_path}")
            except PermissionError:
                # Wait briefly and retry on permission error
                await asyncio.sleep(1)
                path.unlink()
                logger.info(f"Cleaned up file after retry: {file_path}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")
        raise

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    _: Optional[str] = Depends(RateLimiter(times=10, seconds=60))  # 10 requests per minute
) -> Dict[str, str]:
    """Upload a file for processing with rate limiting"""
    try:
        # Validate file size (10MB limit)
        file_size = 0
        chunk_size = 8192
        
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if file_size > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(
                    status_code=413,
                    detail="File too large. Maximum size is 10MB"
                )
        
        await file.seek(0)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(chunk_size):
                await f.write(chunk)
        
        logger.info(f"Uploaded file: {file_path}")
        return {"file_path": str(file_path)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process")
async def process_document(
    file_path: str,
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    _: Optional[str] = Depends(RateLimiter(times=5, seconds=60))  # 5 requests per minute
) -> Dict[str, Any]:
    """Process a document with rate limiting"""
    try:
        # Validate file exists
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Add cleanup task
        background_tasks.add_task(cleanup_uploaded_file, file_path)
        
        # Process document
        result = await orchestrator.process_document(
            document_path=file_path,
            template_name=request.template_name,
            additional_context=request.additional_context
        )
        
        logger.info(f"Processed document: {result.workflow_id}")
        return {
            "workflow_id": result.workflow_id,
            "status": result.status,
            "visio_path": result.visio_file_path,
            "pdf_path": result.pdf_file_path
        }
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        background_tasks.add_task(cleanup_uploaded_file, file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{workflow_id}")
async def get_workflow_status(workflow_id: str) -> Dict[str, Any]:
    """Get workflow status"""
    try:
        # Query RAG memory for workflow record
        results = rag_memory.query_memory(
            query="",
            filters={
                "type": "workflow_record",
                "workflow_id": workflow_id
            },
            limit=1
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Parse workflow record
        record = json.loads(results[0].content)
        
        return {
            "workflow_id": workflow_id,
            "status": record["status"],
            "steps": record["steps"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{workflow_id}/{file_type}")
async def download_file(
    workflow_id: str,
    file_type: FileType,
    _: Optional[str] = Depends(RateLimiter(times=20, seconds=60))  # 20 requests per minute
) -> FileResponse:
    """Download generated file with rate limiting and type validation"""
    try:
        # Get file path based on enum
        file_path = Path(f"data/output/{workflow_id}.{file_type.value}")
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Validate file size
        if file_path.stat().st_size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=413,
                detail="File too large for download"
            )
        
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest) -> Dict[str, str]:
    """Submit user feedback"""
    try:
        entry_id = await self_learning_service.process_feedback(
            feedback_type=request.feedback_type,
            input_data=request.input_data,
            expected_output=request.expected_output,
            actual_output=request.actual_output,
            user_feedback=request.user_feedback,
            confidence_score=request.confidence_score,
            additional_metadata={
                "workflow_id": request.workflow_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Processed feedback: {entry_id}")
        return {"feedback_id": entry_id}
        
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates")
async def list_templates() -> List[str]:
    """List available Visio templates"""
    try:
        templates_dir = Path("data/templates")
        templates = [f.stem for f in templates_dir.glob("*.vstx")]
        return templates
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/ai")
async def get_ai_config() -> Dict[str, Any]:
    """Get AI service configuration"""
    try:
        return {
            "providers": ai_service_manager.list_providers(),
            "models": ai_service_manager.list_models(),
            "current_config": ai_service_manager.get_config()
        }
        
    except Exception as e:
        logger.error(f"Error getting AI config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config/ai")
async def update_ai_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Update AI service configuration"""
    try:
        ai_service_manager.update_config(config)
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error updating AI config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 