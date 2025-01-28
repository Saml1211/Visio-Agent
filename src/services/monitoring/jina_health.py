from fastapi import APIRouter
from jina import Client
from config.jina_settings import JINA_CONFIG

router = APIRouter()
client = Client(host="jina:54321", **JINA_CONFIG)

@router.get("/health/jina")
async def jina_health():
    try:
        status = client.is_flow_ready(timeout=5)
        return {
            "status": "ready" if status else "warming_up",
            "connections": client.num_connections,
            "throughput": client.monitor.throughput
        }
    except Exception as e:
        return {"status": "unreachable", "error": str(e)} 