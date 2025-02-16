"""
Test cases for ContentExtractor.

This module contains test cases for the ContentExtractor class, which is responsible
for extracting various types of content from HTML pages.
"""

# Import built-in modules
import os
from typing import AsyncGenerator

# Import third-party modules
import pytest
from bs4 import BeautifulSoup

# Import local modules
from crawler.data_processor.content_extractor import ContentExtractor, ImageInfo

@pytest.fixture
async def content_extractor() -> AsyncGenerator[ContentExtractor, None]:
    """Create a ContentExtractor instance for testing.
    
    Yields:
        ContentExtractor: The content extractor instance.
    """
    extractor = ContentExtractor()
    yield extractor
    await extractor.close()

@pytest.mark.asyncio
async def test_content_extractor_init(content_extractor: ContentExtractor) -> None:
    """Test ContentExtractor initialization."""
    assert content_extractor is not None

@pytest.mark.asyncio
async def test_extract_images(content_extractor: ContentExtractor) -> None:
    """Test image extraction functionality."""
    html = """
    <html>
        <body>
            <img src="test.jpg" alt="Test Image">
            <img src="test2.png" alt="Test Image 2">
        </body>
    </html>
    """
    images = await content_extractor.extract_images(html, "http://example.com", download=False)
    assert len(images) == 2
    assert all(isinstance(img, ImageInfo) for img in images)
    assert all(img.url.startswith("http://example.com") for img in images)

@pytest.mark.asyncio
async def test_extract_text(content_extractor: ContentExtractor) -> None:
    """Test text extraction functionality."""
    html = """
    <html>
        <body>
            <h1>Test Title</h1>
            <p>Test paragraph</p>
        </body>
    </html>
    """
    text = await content_extractor.extract_text(html)
    assert "Test Title" in text
    assert "Test paragraph" in text

@pytest.mark.asyncio
async def test_extract_structured_data(content_extractor: ContentExtractor) -> None:
    """Test structured data extraction functionality."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Test Title</h1>
        </body>
    </html>
    """
    data = await content_extractor.extract_structured_data(html)
    assert data["title"] == "Test Page"
    assert data["meta_description"] == "Test description"
    assert "Test Title" in data["headings"]["h1"]

@pytest.mark.asyncio
async def test_extract_videos(content_extractor: ContentExtractor) -> None:
    """
    Test video extraction functionality.
    
    Tests:
    1. Regular video files with single source
    2. Videos with multiple sources
    3. Different video formats (mp4, ogg)
    """
    html = """
    <html>
        <body>
            <!-- Video with single source -->
            <video width="320" height="240" controls>
                <source src="https://www.w3schools.com/tags/movie.mp4" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            
            <!-- Direct video tag -->
            <video src="https://www.w3schools.com/html/horse.ogg" controls>
                Your browser does not support the video element.
            </video>
        </body>
    </html>
    """
    
    videos = await content_extractor.extract_videos(
        html=html,
        base_url="https://www.w3schools.com",
        download=False
    )
    
    # Test total number of videos found
    assert len(videos) == 2
    
    # Convert list to dict for easier testing
    video_map = {v["url"]: v for v in videos}
    
    # Test HTML5 demo video
    html5_video = video_map.get("https://www.w3schools.com/tags/movie.mp4")
    assert html5_video is not None
    assert html5_video["type"] == ".mp4"
    assert html5_video["source"] == "video"
    
    # Test direct video tag
    horse_video = video_map.get("https://www.w3schools.com/html/horse.ogg")
    assert horse_video is not None
    assert horse_video["type"] == ".ogg"
    assert horse_video["source"] == "video"
