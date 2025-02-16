"""
Example script for crawling images from Dribbble using the quant_crawler framework.
"""
import os
import asyncio
import aiohttp
import platform
import nest_asyncio
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from quant_crawler.crawler_core.spider import Spider
from quant_crawler.crawler_core.request_manager import RequestManager
from quant_crawler.data_processor.content_extractor import ContentExtractor
from quant_crawler.crawler_core.rate_limiter import RateLimiter
from loguru import logger

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

class DribbbleCrawler:
    """Dribbble crawler implementation."""
    
    def __init__(
        self,
        save_dir: str = "images",
        max_size_mb: int = 50,
        supported_types: List[str] = None
    ):
        """
        Initialize Dribbble crawler.
        
        Args:
            save_dir: Directory to save downloaded images
            max_size_mb: Maximum image size in MB to download
            supported_types: List of supported image file extensions
        """
        self.save_dir = save_dir
        self.max_size_mb = max_size_mb
        self.supported_types = supported_types or ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        # Set up logging
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"dribbble_crawler_{datetime.now():%Y%m%d_%H%M%S}.log")
        logger.add(log_file, rotation="100 MB", retention="30 days")
        
        # Create save directory
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    async def crawl_images(
        self,
        session: aiohttp.ClientSession,
        url: str,
        download: bool = True,
        headers: Dict[str, str] = None,
        request_delay: float = 1.0,
        start_page: int = 1,
        max_pages: int = 1,
        page_param: str = "page",
        image_selector: str = None
    ) -> List[Dict[str, Any]]:
        """
        Crawl images from webpages with pagination support.
        
        Args:
            session: aiohttp client session
            url: Target webpage URL or base URL for pagination
            download: Whether to download the images
            headers: Custom HTTP headers
            request_delay: Delay between requests in seconds
            start_page: Starting page number for pagination
            max_pages: Maximum number of pages to crawl
            page_param: URL parameter for page number
            image_selector: CSS selector for finding image elements
            
        Returns:
            List of image information dictionaries
        """
        try:
            # Initialize components with session
            request_manager = RequestManager()
            request_manager._session = session
            spider = Spider(request_manager)
            content_extractor = ContentExtractor()
            content_extractor._session = session
            rate_limiter = RateLimiter()
            
            # Set custom headers if provided
            if headers:
                request_manager.headers = headers
            
            # Set rate limit
            domain = url.split('/')[2]  # Extract domain from URL
            rate_limiter.update_rate(domain, request_delay)
            
            def parse_image_urls(html: str) -> List[str]:
                """Parse image URLs from HTML content."""
                soup = BeautifulSoup(html, 'html.parser')
                image_elements = []
                
                # Find image elements using selector if provided
                if image_selector:
                    image_elements = soup.select(image_selector)
                else:
                    # Default image element search
                    image_elements = soup.find_all('img')
                
                # Extract URLs
                urls = []
                for element in image_elements:
                    src = element.get('src') or element.get('data-src')
                    if src:
                        urls.append(src)
                
                return urls
            
            # Crawl pages with pagination
            all_images = []
            page_contents = await spider.crawl_with_pagination(
                base_url=url,
                page_parser=parse_image_urls,
                start_page=start_page,
                max_pages=max_pages,
                page_param=page_param
            )
            
            # Extract and download images from each page
            for content in page_contents:
                if not content:
                    continue
                
                images = await content_extractor.extract_images(
                    html=content['html'],
                    base_url=content['url'],
                    save_dir=self.save_dir if download else None,
                    download=download
                )
                
                # Log results
                logger.info(f"Found {len(images)} images on {content['url']}")
                for image in images:
                    logger.info(f"Image: {image['title'] or image['url']}")
                    if image['local_path']:
                        logger.info(f"Downloaded to: {image['local_path']}")
                
                all_images.extend(images)
            
            return all_images
            
        except Exception as e:
            logger.error(f"Error crawling images: {e}")
            return []

async def run():
    """Run the Dribbble crawler."""
    # Initialize crawler
    crawler = DribbbleCrawler(
        save_dir="downloaded_images",
        max_size_mb=50,
        supported_types=['.jpg', '.jpeg', '.png', '.gif', '.webp']
    )
    
    # Example headers (customize as needed)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Example URLs (replace with actual URLs)
    urls = [
        "https://dribbble.com/shots/popular"  # Dribbble 热门页面
    ]
    
    try:
        # Create a single session for all requests
        async with aiohttp.ClientSession() as session:
            # Crawl with pagination
            if urls:
                images = await crawler.crawl_images(
                    session=session,
                    url=urls[0],
                    download=True,
                    headers=headers,
                    request_delay=1.0,
                    start_page=1,
                    max_pages=3,  # 爬取3页
                    page_param="page",  # URL中的页码参数名
                    image_selector="img.shot-thumbnail-img"  # Dribbble 缩略图选择器
                )
                
                print(f"\nFound {len(images)} images in total")
                for image in images:
                    print(f"\nImage: {image['title'] or image['url']}")
                    print(f"Type: {image['type']}")
                    print(f"Size: {image['size']} bytes")
                    if image['local_path']:
                        print(f"Saved to: {image['local_path']}")
    
    except Exception as e:
        print(f"Error running crawler: {e}")

def main():
    """Main entry point."""
    try:
        if platform.system() == 'Windows':
            # 在 Windows 上使用 ProactorEventLoop
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
