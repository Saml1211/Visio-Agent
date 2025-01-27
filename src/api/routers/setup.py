from http.client import HTTPException
import os
from fastapi import APIRouter, HTTPException
from src.services.secure_config import ConfigManager

router = APIRouter()
config_manager = ConfigManager()

@router.post("/setup")
async def complete_setup(config: dict):
    # Validate configuration
    if 'dbPath' not in config:
        raise HTTPException(status_code=400, detail="Missing database path")
    if not validate_db_path(config['dbPath']):
        raise HTTPException(status_code=400, detail="Invalid database path")

    try:
        config_manager.save_config(config)
        os.environ.update({
            "SUPABASE_URL": config['supabaseUrl'],
            "SUPABASE_KEY": config['supabaseKey'],
            "DATA_PATH": config['dbPath']
        })
        return {"status": "configured"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 