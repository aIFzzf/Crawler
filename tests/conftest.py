"""Pytest configuration file."""
import pytest
from crawler.crawler_core import RequestManager, Spider
from crawler.data_processor import ContentExtractor
import aiohttp
import asyncio
import platform

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def aiohttp_session():
    """Create a session for testing."""
    async with aiohttp.ClientSession() as session:
        yield session
