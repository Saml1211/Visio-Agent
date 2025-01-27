from typing import Dict, Any, Optional
import logging
from .base_service import BaseService, ServiceUnavailableError
import httpx

logger = logging.getLogger(__name__)

class DeepseekService(BaseService):
    """Service for interacting with Deepseek's API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()
        self.client = httpx.AsyncClient(timeout=60.0)
        self.base_url = "https://api.deepseek.com/v1"
        
    async def initialize(self) -> None:
        """Initialize the Deepseek service"""
        if not self.api_key:
            raise ServiceUnavailableError("Deepseek API key not configured")
            
    async def cleanup(self) -> None:
        """Cleanup resources"""
        await self.client.aclose()
        
    async def process(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a request through Deepseek's API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "context": context or {},
                "max_tokens": 2048,
                "temperature": 0.7
            }
            
            async with self.client.post(
                f"{self.base_url}/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                result = response.json()
                
                return {
                    "response": result["choices"][0]["text"],
                    "metadata": {
                        "model": result.get("model"),
                        "usage": result.get("usage", {})
                    }
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Deepseek API request failed: {str(e)}")
            raise ServiceUnavailableError(f"Deepseek service error: {str(e)}")
            
    async def health_check(self) -> bool:
        """Check if the service is available"""
        try:
            async with self.client.get(
                f"{self.base_url}/health",
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Deepseek health check failed: {str(e)}")
            return False
            
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment"""
        import os
        return os.getenv("DEEPSEEK_API_KEY") 