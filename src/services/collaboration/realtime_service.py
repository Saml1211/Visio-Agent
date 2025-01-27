from supabase import create_client, Client
from supabase.realtime import Client as RealtimeClient

class RealtimeCollaboration:
    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.realtime = RealtimeClient(os.getenv("SUPABASE_REALTIME_URL"))
        self.channels = {}
        
    async def subscribe(self, diagram_id: str):
        channel = self.realtime.channel(f"diagram:{diagram_id}")
        
        # Presence tracking
        await channel.on_presence_sync(lambda _: self._handle_presence())
        await channel.subscribe()
        
        # Store reference
        self.channels[diagram_id] = channel
        
    async def broadcast_cursor(self, diagram_id: str, position: dict):
        await self.channels[diagram_id].send({
            'type': 'broadcast',
            'event': 'cursor_update',
            'payload': {
                'user_id': self.client.auth.current_user.id,
                'position': position
            }
        })
        
    async def track_changes(self, diagram_id: str, callback):
        await self.channels[diagram_id].on('update', callback) 