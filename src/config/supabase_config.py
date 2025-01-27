from supabase import create_client
import os
from supabase.lib.client_options import ClientOptions
from supabase.lib.realtime_client_options import RealtimeClientOptions

class SupabaseAI:
    def __init__(self):
        self.client = create_configured_client()
        
    async def store_embedding(self, vector: list, metadata: dict):
        return await self.client.rpc('store_embedding', {
            'vector': vector,
            'metadata': metadata
        }) 

def get_client_options():
    return ClientOptions(
        postgrest_client_timeout=15,
        storage_client_timeout=20,
        realtime_options=RealtimeClientOptions(
            timeout=15,
            heartbeat_interval=10
        ),
        schema='public'
    )

def create_configured_client():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY"),
        options=get_client_options()
    ) 