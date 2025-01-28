from langgraph.checkpoint import PostgresCheckpointer
import os

class VisioCheckpointer(PostgresCheckpointer):
    def __init__(self):
        super().__init__(
            conn_string=os.getenv("DB_URI"),
            ttl=3600  # 1 hour TTL
        )
        
    def get_state(self, workflow_id: str):
        return super().get(f"visio_workflow:{workflow_id}")
    
    def save_state(self, workflow_id: str, state: dict):
        return super().put(
            key=f"visio_workflow:{workflow_id}",
            value=state
        ) 