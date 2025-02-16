from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path
import platform

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Core settings
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    WORKERS: int = 1
    
    # API settings
    API_BASE_URL: str = "http://localhost:8080"
    REACT_APP_API_BASE_URL: str = "http://localhost:8080"
    
    # Security
    JWT_SECRET: str
    CONFIG_KEY: str
    
    # AI Service Integrations
    OPENAI_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    
    # Operational Settings
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = "logs/app.log"
    
    # Database
    DB_PASSWORD: str
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    VISIO_HOST: str = "http://localhost:4200"
    
    # Paths
    DATA_PATH: Path = Path("./data")
    MEMORY_PATH: Path = Path("data/memory")
    TEMPLATES_DIR: Path = Path("data/templates")
    STENCILS_DIR: Path = Path("data/stencils")
    OUTPUT_DIR: Path = Path("data/output")
    UPLOAD_DIR: Path = Path("temp/uploads")
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Visio Configuration
    MAX_ZOOM_LEVEL: float = 3.0
    MIN_ZOOM_LEVEL: float = 0.5
    VISIO_STYLE_RULES: str = "config/visio_style_rules"
    
    # NiceGUI settings
    NICEGUI_TITLE: str = "Visio Agent"
    NICEGUI_DARK_MODE: bool = True
    
    # Available tools
    AVAILABLE_TOOLS: List[str] = [
        "diagram_editor",
        "component_library",
        "system_analyzer",
        "document_processor"
    ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from env file

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Ensure directories exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.MEMORY_PATH.mkdir(parents=True, exist_ok=True)
        self.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        self.STENCILS_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def is_windows(self) -> bool:
        return platform.system() == "Windows"
        
    def validate_visio_config(self) -> bool:
        """Validate Visio-specific configuration"""
        if self.is_windows and not self.VISIO_HOST:
            raise ValueError("VISIO_HOST must be set on Windows")
        return True 