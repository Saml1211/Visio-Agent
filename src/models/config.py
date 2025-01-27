from pymongo import MongoClient

class ConfigDB:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.DB_NAME]
        
    async def update_llm_config(self, config: dict):
        self.db.config.update_one(
            {'_id': 'llm_settings'},
            {'$set': config},
            upsert=True
        ) 