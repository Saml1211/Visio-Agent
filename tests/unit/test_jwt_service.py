import pytest
from src.services.auth.jwt_service import JWTService, TokenSettings

def test_token_lifecycle():
    secret = JWTService.generate_secure_key()
    settings = TokenSettings(secret_key=secret)
    service = JWTService(settings)
    
    token = service.create_token("user123", ["read:data"])
    payload = service.validate_token(SecurityScopes(["read:data"]), token)
    
    assert payload["sub"] == "user123"
    assert "read:data" in payload["scopes"]
    
    with pytest.raises(JWTError):
        service.validate_token(SecurityScopes(["write:data"]), token) 