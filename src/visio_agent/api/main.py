from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ..config.settings import Settings
from ..services.service_registry import ServiceRegistry
from .routers import diagrams, tools, workflow

# Initialize settings and services
settings = Settings()
service_registry = ServiceRegistry()

# Create FastAPI app
app = FastAPI(
    title="Visio Agent",
    description="AI-powered system for automating AV system diagrams",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diagrams.router, prefix="/api/diagrams", tags=["diagrams"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION} 