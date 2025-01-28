import pytest
from src.services.auth.jwt_service import SecurityConfig

@pytest.mark.production
def test_production_security_settings():
    config = SecurityConfig()
    
    assert config.JWT_ALGORITHM == "HS256"
    assert len(config.JWT_SECRET) >= 32
    assert config.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    
def test_cors_origins():
    with open('.cursorrules') as f:
        content = f.read()
    
    assert "https://app.visio-automation.com" in content
    assert "https://collab.visio-automation.com" in content
    assert "http://localhost" not in content 