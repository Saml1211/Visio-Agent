from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> User:
    """
    For development, return a mock user without authentication.
    In production, this would validate the token and return the actual user.
    """
    return User(
        id="dev_user",
        username="developer",
        email="dev@example.com",
        is_admin=True
    ) 