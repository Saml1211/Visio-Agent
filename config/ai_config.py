import os
from typing import Dict, Any

class AIServiceConfig:
    def __init__(self):
        self.vector_stores: Dict[str, Dict[str, Any]] = {
            'pinecone': {
                'api_key': os.getenv('PINECONE_API_KEY'),
                'environment': 'us-west1-gcp',
                'index_name': 'main'
            },
            'chroma': {
                'persist_path': './chroma_db'
            }
        }
        
        self.schema_config = {
            'schemas_dir': 'config/schemas/',
            'default_schema': 'lld_schema.json'
        } 