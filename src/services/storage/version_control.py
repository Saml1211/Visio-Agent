from datetime import datetime

class VersionControl:
    def __init__(self):
        self.client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    async def save_version(self, diagram: VisioDocument):
        version_id = str(uuid4())
        try:
            # Store binary
            storage_response = self.client.storage.from_("diagram_versions").upload(
                f"{version_id}.vsdx",
                diagram.to_bytes(),
                {
                    'content-type': 'application/vnd.visio',
                    'cache-control': 'max-age=31536000'
                }
            )
            
            # Store metadata
            metadata = {
                "diagram_id": diagram.id,
                "version_id": version_id,
                "created_at": datetime.utcnow().isoformat(),
                "author": diagram.author,
                "components": len(diagram.components),
                "routing_algorithm": diagram.routing_algorithm,
                "style_hash": diagram.style_hash
            }
            
            await self.client.table('versions').insert(metadata).execute()
            return version_id
            
        except Exception as e:
            logger.error(f"Version save failed: {str(e)}")
            raise 