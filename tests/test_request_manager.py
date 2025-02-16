"""Test cases for RequestManager."""
import pytest
import aiohttp
from quant_crawler.crawler_core.request_manager import RequestManager

@pytest.mark.asyncio
async def test_request_manager_init():
    """Test RequestManager initialization."""
    manager = RequestManager()
    assert manager.headers is not None
    assert isinstance(manager.headers, dict)

@pytest.mark.asyncio
async def test_request_manager_get():
    """Test RequestManager get method."""
    manager = RequestManager()
    async with aiohttp.ClientSession() as session:
        manager._session = session
        response = await manager.get("https://www.w3schools.com")
        assert response is not None
        assert isinstance(response, str)

@pytest.mark.asyncio
async def test_request_manager_headers():
    """Test RequestManager headers."""
    manager = RequestManager()
    custom_headers = {
        "User-Agent": "Test Agent",
        "Accept": "text/html"
    }
    manager.headers = custom_headers
    assert manager.headers == custom_headers
