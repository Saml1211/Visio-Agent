import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
import os
import asyncio
from unittest.mock import patch, MagicMock

from src.api.main import app, cleanup_uploaded_file, FileType

client = TestClient(app)

@pytest.fixture
def temp_upload_file():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        yield tmp.name
    # Cleanup happens in the test

@pytest.fixture
def large_temp_file():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # Create 11MB file
        tmp.write(b"0" * (11 * 1024 * 1024))
        yield tmp.name
    try:
        os.unlink(tmp.name)
    except:
        pass

@pytest.fixture
def mock_redis():
    with patch("src.api.main.redis_client") as mock:
        yield mock

async def test_cleanup_uploaded_file_success(temp_upload_file):
    # Verify file exists
    assert Path(temp_upload_file).exists()
    
    # Run cleanup
    await cleanup_uploaded_file(temp_upload_file)
    
    # Verify file is deleted
    assert not Path(temp_upload_file).exists()

async def test_cleanup_uploaded_file_retry(temp_upload_file):
    # Mock permission error on first attempt
    call_count = 0
    original_unlink = Path.unlink
    
    def mock_unlink(self):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise PermissionError("Permission denied")
        return original_unlink(self)
    
    with patch.object(Path, "unlink", mock_unlink):
        await cleanup_uploaded_file(temp_upload_file)
    
    assert call_count == 2
    assert not Path(temp_upload_file).exists()

async def test_upload_file_size_limit(large_temp_file):
    with open(large_temp_file, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", f)}
        )
    
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]

async def test_upload_file_unique_name():
    content = b"test content"
    responses = []
    
    # Upload same file twice
    for _ in range(2):
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", content)}
        )
        responses.append(response.json()["file_path"])
    
    assert responses[0] != responses[1]
    
    # Cleanup
    for path in responses:
        try:
            os.unlink(path)
        except:
            pass

async def test_process_document_file_not_found():
    response = client.post(
        "/api/process",
        json={
            "file_path": "nonexistent.txt",
            "template_name": "test_template"
        }
    )
    
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]

async def test_download_file_size_limit():
    # Create large test file
    workflow_id = "test_workflow"
    file_path = Path(f"data/output/{workflow_id}.vsdx")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(b"0" * (51 * 1024 * 1024))
    
    try:
        response = client.get(f"/api/download/{workflow_id}/{FileType.VISIO}")
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]
    finally:
        try:
            file_path.unlink()
        except:
            pass

async def test_rate_limiting(mock_redis):
    # Mock rate limiter to simulate limit exceeded
    mock_redis.incr.return_value = 11  # Exceed upload limit
    
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", b"content")}
    )
    
    assert response.status_code == 429  # Too Many Requests 