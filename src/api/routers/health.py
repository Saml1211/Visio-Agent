from fastapi import APIRouter, status
from typing import Dict
import platform

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict:
    """Check health of all services"""
    registry = ServiceRegistry()
    services_status = {}
    
    for service_name in registry.services:
        try:
            service = registry.get(service_name)()
            # Simple ping test
            await service.execute({"ping": True})
            services_status[service_name] = "healthy"
        except Exception as e:
            services_status[service_name] = f"unhealthy: {str(e)}"
    
    return {
        "status": "operational",
        "platform": platform.system(),
        "services": services_status
    } 