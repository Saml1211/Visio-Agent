import os
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException
from pydantic import BaseSettings, Field
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta
import logging
from jose import JWTError, jwt
from passlib.context import CryptContext
from multi_agent_orchestrator import OrchestratorClaims
from langgraph.security import GraphPolicy
from starlette import status

# Configure structured JSON logging
logger = logging.getLogger(__name__)

class JWTSettings(BaseSettings):
    secret_key: str = Field(..., env="JWT_SECRET_KEY")
    algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = JWTSettings()

security = HTTPBearer()

async def get_current_user(credentials: HTTPBearer = Depends(security)):
    try:
        # Verify JWT with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

async def create_jwt_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Creates a JWT token with proper expiration and security settings
    
    Args:
        data: Dictionary containing payload data
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        str: Encoded JWT token
        
    Raises:
        HTTPException: If token creation fails
    """
    try:
        settings = JWTSettings()
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(
            minutes=settings.access_token_expire_minutes
        ))
        to_encode.update({"exp": expire})
        
        logger.info("Creating JWT token", extra={
            "event": "jwt_creation",
            "user": data.get("sub"),
            "expiration": expire.isoformat()
        })
        
        return jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm
        )
        
    except (jwt.PyJWTError, ValueError) as e:
        logger.error("JWT creation failed", exc_info=True, extra={
            "error": str(e),
            "user": data.get("sub")
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token creation failed"
        )

async def validate_jwt_token(token: str) -> Dict[str, Any]:
    """
    Validates and decodes a JWT token with proper error handling
    
    Args:
        token: JWT token string to validate
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        HTTPException: For various validation errors
    """
    try:
        settings = JWTSettings()
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        logger.info("JWT validation successful", extra={
            "event": "jwt_validation",
            "user": payload.get("sub")
        })
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except (jwt.InvalidTokenError, jwt.DecodeError) as e:
        logger.warning("Invalid JWT token attempted", extra={
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Add MAO-specific claims
OrchestratorClaims.add_required_claims(
    "visio_generate", 
    "diagram_validate",
    "collaboration_write"
)

# Configure LangGraph security policy
GraphPolicy.register(
    "visio_workflow",
    requires=["visio:generate", "workflow:manage"]
) 