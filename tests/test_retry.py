"""Tests for retry functionality"""

import pytest
import asyncio
from unittest.mock import Mock
import time

from src.utils.retry import with_retry
from src.services.exceptions import ChatbotError, ServiceError, RateLimitError

# Test async function that fails N times then succeeds
async def async_fail_n_times(n: int, mock_fn=None):
    if mock_fn:
        mock_fn()
    if n > 0:
        raise ServiceError(f"Failing {n} more times")
    return "success"

# Test sync function that fails N times then succeeds
def sync_fail_n_times(n: int, mock_fn=None):
    if mock_fn:
        mock_fn()
    if n > 0:
        raise ServiceError(f"Failing {n} more times")
    return "success"

@pytest.mark.asyncio
async def test_async_retry_success():
    """Test successful async retry"""
    mock_fn = Mock()
    
    # Function that fails twice then succeeds
    @with_retry(retries=3, delay=0.1)
    async def test_fn():
        return await async_fail_n_times(2, mock_fn)
    
    result = await test_fn()
    assert result == "success"
    assert mock_fn.call_count == 3  # Called until success

@pytest.mark.asyncio
async def test_async_retry_failure():
    """Test async retry exhaustion"""
    mock_fn = Mock()
    
    # Function that fails more times than retries
    @with_retry(retries=2, delay=0.1)
    async def test_fn():
        return await async_fail_n_times(3, mock_fn)
    
    with pytest.raises(ServiceError):
        await test_fn()
    assert mock_fn.call_count == 2  # Called until retries exhausted

def test_sync_retry_success():
    """Test successful sync retry"""
    mock_fn = Mock()
    
    # Function that fails twice then succeeds
    @with_retry(retries=3, delay=0.1)
    def test_fn():
        return sync_fail_n_times(2, mock_fn)
    
    result = test_fn()
    assert result == "success"
    assert mock_fn.call_count == 3  # Called until success

def test_sync_retry_failure():
    """Test sync retry exhaustion"""
    mock_fn = Mock()
    
    # Function that fails more times than retries
    @with_retry(retries=2, delay=0.1)
    def test_fn():
        return sync_fail_n_times(3, mock_fn)
    
    with pytest.raises(ServiceError):
        test_fn()
    assert mock_fn.call_count == 2  # Called until retries exhausted

@pytest.mark.asyncio
async def test_async_rate_limit_retry():
    """Test retry with rate limit error"""
    mock_fn = Mock()
    calls = 0
    
    @with_retry(retries=3, delay=0.1)
    async def test_fn():
        nonlocal calls
        mock_fn()
        calls += 1
        if calls == 1:
            raise RateLimitError("Rate limit", retry_after=0.1)
        return "success"
    
    result = await test_fn()
    assert result == "success"
    assert mock_fn.call_count == 2  # Called until success

def test_no_retry_on_unexpected_error():
    """Test that unexpected errors are not retried"""
    mock_fn = Mock()
    
    @with_retry(retries=3, delay=0.1)
    def test_fn():
        mock_fn()
        raise ValueError("Unexpected error")
    
    with pytest.raises(ValueError):
        test_fn()
    assert mock_fn.call_count == 1  # Called only once 