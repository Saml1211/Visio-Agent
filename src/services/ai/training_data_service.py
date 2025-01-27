from sentence_transformers import SentenceTransformer

class TrainingDataService:
    def __init__(self):
        self.client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def store_successful_route(self, route: dict):
        try:
            # Generate embedding
            route_text = f"{route['algorithm']} {route['constraints']}"
            embedding = self.encoder.encode(route_text).tolist()
            
            await self.client.table('ai_training_data').insert({
                'type': 'successful_route',
                'embedding': embedding,
                'metadata': {
                    'components': route['components'],
                    'execution_time': route['execution_time'],
                    'crossings': route['crossings']
                }
            }).execute()
            
        except Exception as e:
            logger.error(f"Failed to store training data: {str(e)}")
            raise 