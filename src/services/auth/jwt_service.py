import os
from typing import Optional
import jwt
from fastapi import HTTPException
from pydantic import BaseSettings
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from datetime import datetime, timedelta
import logging

class SecurityConfig(BaseSettings):
    JWT_SECRET: str = os.getenv("JWT_SECRET", "unsafe_default_secret")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

config = SecurityConfig()

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(credentials: HTTPBearer = Depends(security)):
    try:
        # Verify JWT with Supabase
        user = supabase.auth.get_user(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

def create_jwt_token(data: dict) -> str:
    try:
        return jwt.encode(
            {**data, "exp": datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)},
            config.JWT_SECRET,
            algorithm=config.JWT_ALGORITHM
        )
    except Exception as e:
        logger.error(f"JWT Creation Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token creation failed")

def verify_jwt_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token, 
            config.JWT_SECRET, 
            algorithms=[config.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token attempted")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError as e:
        logger.warning(f"Invalid JWT: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token") 