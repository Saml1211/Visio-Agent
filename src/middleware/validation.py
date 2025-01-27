from fastapi import Request, HTTPException
from typing import Callable

async def validate_model_config(request: Request, call_next: Callable):
    if request.url.path == '/api/update-config':
        config = await request.json()
        # Validate enabled models
        if sum(config[m]['enabled'] for m in ['deepseek','gemini','openai']) == 0:
            raise HTTPException(400, "At least one model must be enabled")
            
    return await call_next(request) 