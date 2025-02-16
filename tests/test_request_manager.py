"""
Test cases for RequestManager.

This module contains test cases for the RequestManager class, which is responsible
for handling HTTP requests.
"""

# Import built-in modules
from typing import AsyncGenerator

# Import third-party modules
import pytest
import aiohttp

# Import local modules
from crawler.crawler_core.request_manager import RequestManager

@pytest.fixture
async def request_manager() -> AsyncGenerator[RequestManager, None]:
    """Create a RequestManager instance for testing.
    
    Yields:
        RequestManager: The request manager instance.
    """
    manager = RequestManager()
    yield manager
    await manager.close()

@pytest.mark.asyncio
async def test_request_manager_init(request_manager: RequestManager) -> None:
    """Test RequestManager initialization."""
    assert request_manager is not None
    assert isinstance(request_manager.headers, dict)
    assert "User-Agent" in request_manager.headers
    assert request_manager.max_retries == 3
    assert request_manager.delay == 1

@pytest.mark.asyncio
async def test_request_manager_get(request_manager: RequestManager) -> None:
    """Test GET request functionality."""
    url = "https://www.google.com.hk/"
    response = await request_manager.make_request(url)
    assert isinstance(response, str)
    assert "html" in response.lower()

@pytest.mark.asyncio
async def test_request_manager_set_proxy(request_manager: RequestManager) -> None:
    """Test proxy setting functionality."""
    proxy = "http://localhost:8080"
    request_manager.set_proxy(proxy)
    assert request_manager.proxy == proxy

@pytest.mark.asyncio
async def test_request_manager_set_retry_policy(request_manager: RequestManager) -> None:
    """Test retry policy configuration."""
    max_retries = 5
    delay = 2
    request_manager.set_retry_policy(max_retries, delay)
    assert request_manager.max_retries == max_retries
    assert request_manager.delay == delay

@pytest.mark.asyncio
async def test_request_manager_with_custom_headers(request_manager: RequestManager) -> None:
    """Test request with custom headers."""
    url = "https://www.google.com.hk/"
    custom_headers = {"Accept-Language": "zh-CN,zh;q=0.9"}
    response = await request_manager.make_request(url, headers=custom_headers)
    assert isinstance(response, str)
    assert "html" in response.lower()
