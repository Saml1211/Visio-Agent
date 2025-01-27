from fastapi import APIRouter
from src.services.monitoring import PerformanceMonitor

router = APIRouter()
monitor = PerformanceMonitor()

@router.get("/performance-metrics")
async def get_performance_metrics():
    return monitor.get_metrics() 