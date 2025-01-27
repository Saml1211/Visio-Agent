from supabase import create_client
import os
from uuid import uuid4

class DiagramStorage:
    def __init__(self):
        self.client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    async def save_diagram(self, vsdx_data: bytes, metadata: dict):
        file_name = f"{uuid4()}.vsdx"
        self.client.storage.from_("diagrams").upload(file_name, vsdx_data)
        self.client.table("diagram_metadata").insert(metadata).execute() 