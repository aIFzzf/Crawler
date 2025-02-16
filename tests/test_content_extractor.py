"""Test cases for ContentExtractor."""
import pytest
from quant_crawler.data_processor.content_extractor import ContentExtractor

@pytest.mark.asyncio
async def test_content_extractor_init():
    """Test ContentExtractor initialization."""
    extractor = ContentExtractor()
    assert extractor is not None

@pytest.mark.asyncio
async def test_extract_images():
    """Test image extraction."""
    extractor = ContentExtractor()
    html = """
    <html>
        <body>
            <img src="test.jpg" alt="Test Image">
            <img src="test2.png" alt="Test Image 2">
        </body>
    </html>
    """
    images = await extractor.extract_images(html, "http://example.com", download=False)
    assert len(images) == 2
    assert all(isinstance(img, dict) for img in images)

@pytest.mark.asyncio
async def test_extract_videos():
    """Test video extraction."""
    extractor = ContentExtractor()
    html = """
    <html>
        <body>
            <video src="test.mp4">
            <source src="test2.webm" type="video/webm">
        </body>
    </html>
    """
    videos = await extractor.extract_videos(html, "http://example.com", download=False)
    assert len(videos) == 2
    assert all(isinstance(video, dict) for video in videos)
