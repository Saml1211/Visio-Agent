from pydantic import BaseSettings, Field
from pathlib import Path

class ServiceConfig(BaseSettings):
    # Browserbase Configuration
    browserbase_api_key: str = Field(..., env="BROWSERBASE_API_KEY")
    browserbase_project_id: str = Field(..., env="BROWSERBASE_PROJECT_ID")
    
    # Screenpipe Configuration
    screenpipe_endpoint: str = Field("wss://api.screenpipe.com/ws", env="SCREENPIPE_ENDPOINT")
    screenpipe_api_key: str = Field(..., env="SCREENPIPE_API_KEY")
    
    # Visio Agent Configuration
    visio_style_rules: Path = Field(Path("config/visio_style_rules"), env="VISIO_STYLE_RULES")
    spec_cache_ttl: int = Field(3600, env="SPEC_CACHE_TTL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

def get_config() -> ServiceConfig:
    return ServiceConfig() 