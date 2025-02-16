"""
Test cases for Spider.

This module contains test cases for the Spider class, which is responsible
for crawling web pages.
"""

# Import built-in modules
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, patch

# Import third-party modules
import pytest
import aiohttp

# Import local modules
from crawler.crawler_core.spider import Spider
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

@pytest.fixture
async def spider(request_manager: RequestManager) -> AsyncGenerator[Spider, None]:
    """Create a Spider instance for testing.
    
    Args:
        request_manager: The request manager instance to use.
        
    Yields:
        Spider: The spider instance.
    """
    spider_instance = Spider(request_manager)
    yield spider_instance

@pytest.mark.asyncio
async def test_spider_initialization(spider: Spider) -> None:
    """Test spider initialization."""
    assert spider is not None
    assert isinstance(spider.request_manager, RequestManager)

@pytest.mark.asyncio
async def test_spider_validate_url() -> None:
    """Test URL validation."""
    request_manager = RequestManager()
    spider = Spider(request_manager)
    
    # Valid URLs
    assert spider.validate_url("http://example.com")
    assert spider.validate_url("https://example.com")
    assert spider.validate_url("https://sub.example.com/path?query=1")
    
    # Invalid URLs
    assert not spider.validate_url("not_a_url")
    assert not spider.validate_url("ftp://example.com")
    assert not spider.validate_url("")

@pytest.mark.asyncio
async def test_spider_crawl_with_mock() -> None:
    """Test spider crawl functionality with mocked request."""
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <a href="http://example.com/link1">Link 1</a>
            <a href="http://example.com/link2">Link 2</a>
        </body>
    </html>
    """
    
    request_manager = RequestManager()
    with patch.object(request_manager, 'make_request', return_value=html_content):
        spider = Spider(request_manager)
        result = await spider.crawl("http://example.com")
        
        assert isinstance(result, dict)
        assert "html" in result
        assert result["html"] == html_content
        assert "url" in result
        assert result["url"] == "http://example.com"
        assert "parsed_data" in result
        assert "title" in result["parsed_data"]
        assert result["parsed_data"]["title"] == "Test Page"
        assert len(result["parsed_data"]["links"]) == 2
