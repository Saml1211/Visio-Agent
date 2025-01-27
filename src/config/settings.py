from pydantic_settings import BaseSettings
from typing import Optional
import platform

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    JWT_SECRET: str
    CONFIG_KEY: str
    VISIO_HOST: Optional[str] = None
    
    class Config:
        env_file = ".env"
        
    @property
    def is_windows(self) -> bool:
        return platform.system() == "Windows"
        
    def validate_visio_config(self) -> bool:
        """Validate Visio-specific configuration"""
        if self.is_windows and not self.VISIO_HOST:
            raise ValueError("VISIO_HOST must be set on Windows")
        return True 