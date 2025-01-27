from httpx import AsyncClient
import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class JinaReaderService:
    def __init__(self):
        self.base_url = "https://r.jina.ai/"
        self.client = AsyncClient(timeout=30.0)
    
    async def read_url(self, url: str) -> Dict:
        """Get clean structured data from any URL using Jina Reader API"""
        try:
            response = await self.client.get(f"{self.base_url}{url}")
            response.raise_for_status()  # Raise for non-200 status codes
            return {
                "content": response.text,
                "format": "markdown",
                "metadata": {
                    "source": url,
                    "jina_processed": True,
                    "content_type": response.headers.get("content-type"),
                    "status_code": response.status_code
                }
            }
        except Exception as e:
            logger.error(f"Jina Reader failed for {url}: {str(e)}")
            raise 