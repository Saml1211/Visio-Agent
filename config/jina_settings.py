# Centralized configuration
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict

class JinaConfig(BaseSettings):
    endpoint: str = Field(
        default="grpc://localhost:54321",
        env="JINA_ENDPOINT"
    )
    timeout: int = Field(
        default=300,
        description="Timeout for Jina operations in seconds"
    )
    embedding_dim: int = Field(
        default=768,
        description="Dimension of Jina embedding model"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="JINA_",
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8"
    )

JINA_API_URL = "https://api.jina.ai"
JINA_TIMEOUT = 30
JINA_MAX_RETRIES = 3
JINA_RATE_LIMIT = "100/60s"  # 100 requests per minute

# Add MAO configuration
MAO_ORCHESTRATOR_CONFIG = {
    "agent_timeout": 30,
    "max_retries": 3,
    "visio_operations": {
        "max_shapes": 500,
        "auto_cleanup": True
    }
}

# Before
JINA_CONFIG = {
    "timeout": 30,
    "max_retries": 3
}

# After
JINA_CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "pool_size": 10,
    "pool_timeout": 60,
    "compression": "gzip",
    "min_compress_size": 1024
}

# Added security headers and rate limiting configuration
# Implemented proper CORS settings

class SecuritySettings(BaseSettings):
    cors_origins: list = ["https://your-domain.com"]
    rate_limit: str = "100/minute"
    enable_hsts: bool = True
    content_security_policy: str = "default-src 'self'"
    
    class Config:
        env_prefix = "SECURITY_"
        env_file = ".env" 