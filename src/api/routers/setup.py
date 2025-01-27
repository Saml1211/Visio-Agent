from fastapi import APIRouter
from src.services.secure_config import ConfigManager

router = APIRouter()
config_manager = ConfigManager()

@router.post("/setup")
async def complete_setup(config: dict):
    # Validate configuration
    if not validate_db_path(config.get('dbPath')):
        raise HTTPException(400, "Invalid database path")
        
    config_manager.save_config(config)
    
    # Update environment
    os.environ.update({
        "SUPABASE_URL": config['supabaseUrl'],
        "SUPABASE_KEY": config['supabaseKey'],
        "DATA_PATH": config['dbPath']
    })
    
    return {"status": "configured"} 