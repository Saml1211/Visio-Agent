from fastapi import APIRouter
from pydantic import BaseModel
from config import settings

router = APIRouter()

class ModelConfig(BaseModel):
    deepseek: dict
    gemini: dict
    openai: dict

@router.post("/update-config")
async def update_config(config: ModelConfig):
    try:
        # Save to database
        await settings.update_llm_config(config.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, f"Config update failed: {str(e)}") 