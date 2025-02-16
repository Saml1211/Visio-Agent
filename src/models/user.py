from pydantic import BaseModel, EmailStr

class User(BaseModel):
    """User model for authentication and authorization."""
    id: str
    username: str
    email: str
    is_admin: bool = False 