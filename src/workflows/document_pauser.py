from retrying import retry, stop_after_attempt, wait_fixed
from datetime import timedelta
from src.services.vector_store.eve_adapter import EveDB
from src.utils.logger import logger

@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
async def store_checkpoint(doc):
    """Enhanced checkpoint storage"""
    try:
        await EveDB.store(
            key=f"checkpoint_{doc.id}",
            value=doc.model_dump(),
            ttl=timedelta(hours=24)
        )
    except Exception as e:
        logger.error(f"Checkpoint save failed: {e}")
        raise 