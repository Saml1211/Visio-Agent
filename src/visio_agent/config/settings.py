"""Application settings module."""

from pydantic_settings import BaseSettings
from typing import List, Optional, Union
from pathlib import Path
import json

class Settings(BaseSettings):
    """Application settings."""
    
    # Core settings
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    JWT_SECRET: str
    API_BASE_URL: str = "http://localhost:8000"
    
    # AI Service Integrations
    OPENAI_API_KEY: str
    HUGGINGFACE_API_KEY: str
    DEEPSEEK_API_KEY: str
    
    # Operational Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1
    
    # Visio Configuration
    MAX_ZOOM_LEVEL: float = 3.0
    MIN_ZOOM_LEVEL: float = 0.5
    VISIO_STYLE_RULES: str = "config/visio_style_rules"
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    DATA_DIR: Path = Path("./data")
    STATIC_DIR: Path = Path("./static")
    MEMORY_PATH: Path = Path("data/memory")
    TEMPLATES_DIR: Path = Path("data/templates")
    STENCILS_DIR: Path = Path("data/stencils")
    OUTPUT_DIR: Path = Path("data/output")
    UPLOAD_DIR: Path = Path("temp/uploads")
    
    # Server Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Database Configuration
    MONGO_URI: str = "mongodb://localhost:27017"
    DB_NAME: str = "visio_agent"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> any:
            if field_name == "CORS_ORIGINS" and raw_val.startswith("["):
                return json.loads(raw_val)
            return raw_val
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Ensure required directories exist
        for path in [
            self.DATA_DIR,
            self.STATIC_DIR,
            self.MEMORY_PATH,
            self.TEMPLATES_DIR,
            self.STENCILS_DIR,
            self.OUTPUT_DIR,
            self.UPLOAD_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True) 