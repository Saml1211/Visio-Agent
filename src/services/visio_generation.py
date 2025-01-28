from langchain.tools import tool
from .visio_controller import VisioController
from functools import lru_cache
from queue import Queue
import win32com.client
from functools import lru_cache
from cachetools import TTLCache

@tool
def generate_visio_diagram(state: VisioWorkflowState):
    """Generates Visio diagram using extracted components"""
    controller = VisioController()
    try:
        diagram_path = controller.generate(
            components=state["visio_components"],
            template=state.get("template", "default")
        )
        return {"diagram_path": diagram_path}
    except Exception as e:
        logger.error(f"Visio generation failed: {str(e)}")
        raise 

class VisioPerformanceOptimizer:
    def __init__(self):
        self.template_cache = TTLCache(maxsize=10, ttl=300)
        
    async def preload_templates(self, template_names: list):
        """Cache frequently used templates"""
        for name in template_names:
            if name not in self.template_cache:
                self.template_cache[name] = self._load_template(name)
                
    def _load_template(self, template_name: str) -> VisioTemplate:
        """Load template with connection pooling"""
        with VisioConnectionPool() as pool:
            return pool.get_template(template_name)

class VisioConnectionPool:
    def __init__(self, max_connections=5):
        self.pool = Queue(max_connections)
        for _ in range(max_connections):
            self.pool.put(win32com.client.Dispatch("Visio.Application"))
            
    def __enter__(self):
        return self.pool.get()
    
    def __exit__(self, type, value, traceback):
        self.pool.put(self.visio_app) 