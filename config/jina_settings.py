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