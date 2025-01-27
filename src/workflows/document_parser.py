from typing import Dict, List, Optional
import logging
from retrying import retry
from src.services.vector_store.eve_adapter import EVEAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DocumentParser:
    def __init__(self):
        self.eve_adapter = EVEAdapter()
        
    @retry(stop_max_attempt_number=3, wait_exponential_multiplier=1000)
    async def parse_document(self, document_path: str) -> Dict:
        """Parse document with retries on failure"""
        try:
            return await self.eve_adapter.process_document(document_path)
        except Exception as e:
            logger.error(f"Failed to parse document: {str(e)}")
            raise 