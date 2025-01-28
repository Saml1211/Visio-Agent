import json
from datetime import datetime
from src.services.websocket_manager import WebSocketManager
from src.services.diagram_version_control import DiagramVersionControl

class RealTimeCollaboration:
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.version_control = DiagramVersionControl()
        
    async def handle_collaboration(self, workflow_id: str):
        """Manage real-time collaboration session"""
        async with self.websocket_manager.connect(workflow_id) as ws:
            while True:
                update = await ws.receive_json()
                await self.version_control.handle_update(
                    workflow_id,
                    update,
                    ws.client_id
                )
                await self.broadcast_update(workflow_id, update)

    async def broadcast_update(self, workflow_id: str, update: dict):
        """Send updates to all connected clients"""
        await self.websocket_manager.broadcast(
            workflow_id,
            json.dumps({
                "type": "diagram_update",
                "data": update,
                "timestamp": datetime.now().isoformat()
            })
        ) 