import pytest
from src.services.auth.jwt_service import create_jwt_token, validate_jwt_token
from fastapi import HTTPException

@pytest.mark.asyncio
async def test_jwt_flow_success():
    test_data = {"sub": "test_user", "role": "admin"}
    token = await create_jwt_token(test_data)
    payload = await validate_jwt_token(token)
    assert payload["sub"] == "test_user"
    assert "exp" in payload

@pytest.mark.asyncio
async def test_expired_token_handling():
    with pytest.raises(HTTPException) as exc:
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjE2MzUwMjQwMDB9.xyz"
        await validate_jwt_token(expired_token)
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail 