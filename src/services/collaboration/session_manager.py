import websockets
from typing import Dict, Set

class CollaborationSession:
    def __init__(self):
        self.connections: Set[websockets.WebSocketServerProtocol] = set()
        self.diagram_state: Dict = {}
        
    async def handle_connection(self, websocket):
        self.connections.add(websocket)
        try:
            async for message in websocket:
                await self._broadcast(message)
        finally:
            self.connections.remove(websocket)
            
    async def _broadcast(self, message):
        for connection in self.connections:
            await connection.send(message) 