from pydantic import BaseSettings

class SecuritySettings(BaseSettings):
    jwt_secret: str = JWTService.generate_secure_key()
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 45
    
    class Config:
        env_file = ".env" 