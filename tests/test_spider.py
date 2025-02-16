"""
Test cases for the Spider component.
"""

import pytest
import aiohttp
from quant_crawler.crawler_core import Spider, RequestManager

@pytest.mark.asyncio
async def test_spider_initialization():
    """Test spider initialization."""
    request_manager = RequestManager()
    spider = Spider(request_manager)
    assert spider is not None
    assert spider.request_manager is request_manager

@pytest.mark.asyncio
async def test_spider_crawl():
    """Test spider crawl functionality."""
    request_manager = RequestManager()
    spider = Spider(request_manager)
    
    # Mock URL for testing
    test_url = "https://example.com"
    
    async with aiohttp.ClientSession() as session:
        content = await spider.crawl(test_url)
        assert content is not None
        assert 'html' in content
        assert isinstance(content['html'], str)
