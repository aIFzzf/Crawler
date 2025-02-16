"""
Example script for crawling videos using the quant_crawler framework.
"""
import os
import asyncio
import aiohttp
import platform
import nest_asyncio
import ssl
import re
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

class VideoCrawler:
    """Video crawler implementation."""
    
    def __init__(
        self,
        save_dir: str = "videos",
        max_size_mb: int = 500,
        supported_types: List[str] = None
    ):
        """
        Initialize video crawler.
        
        Args:
            save_dir: Directory to save downloaded videos
            max_size_mb: Maximum video size in MB to download
            supported_types: List of supported video file extensions
        """
        self.save_dir = save_dir
        self.max_size_mb = max_size_mb
        self.supported_types = supported_types or ['.mp4', '.webm', '.avi']
        
        # Set up logging
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"video_crawler_{datetime.now():%Y%m%d_%H%M%S}.log")
        logger.add(log_file, rotation="100 MB", retention="30 days")
        
        # Create save directory
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    async def get_page_content(
        self,
        session: aiohttp.ClientSession,
        url: str,
        headers: Dict[str, str] = None
    ) -> str:
        """
        Get page content and handle potential popups in the HTML.
        
        Args:
            session: aiohttp client session
            url: URL to get content from
            headers: Custom HTTP headers
            
        Returns:
            Page HTML content with popups removed
        """
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 移除常见的弹窗元素
                    popup_selectors = [
                        '.popup', '.modal', '.dialog', '.overlay',
                        '[class*="popup"]', '[class*="modal"]', '[class*="dialog"]',
                        '[id*="popup"]', '[id*="modal"]', '[id*="dialog"]',
                        'div[style*="position: fixed"]',
                        'div[style*="position:fixed"]',
                        'div[style*="z-index: 9999"]',
                        'div[style*="z-index:9999"]'
                    ]
                    
                    for selector in popup_selectors:
                        for element in soup.select(selector):
                            element.decompose()
                    
                    return str(soup)
                else:
                    logger.error(f"Error getting page content: HTTP {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return ""
    
    async def crawl_videos(
        self,
        session: aiohttp.ClientSession,
        url: str,
        download: bool = True,
        headers: Dict[str, str] = None,
        request_delay: float = 1.0,
        start_page: int = 1,
        max_pages: int = 1,
        page_param: str = "page",
        video_selector: str = None
    ) -> List[Dict[str, Any]]:
        """
        Crawl videos from webpages with pagination support.
        
        Args:
            session: aiohttp client session
            url: Target webpage URL or base URL for pagination
            download: Whether to download the videos
            headers: Custom HTTP headers
            request_delay: Delay between requests in seconds
            start_page: Starting page number for pagination
            max_pages: Maximum number of pages to crawl
            page_param: URL parameter for page number
            video_selector: CSS selector for finding video elements
            
        Returns:
            List of video information dictionaries
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
            
            def parse_video_urls(html: str) -> List[str]:
                """Parse video URLs from HTML content."""
                soup = BeautifulSoup(html, 'html.parser')
                video_elements = []
                
                # Find video elements using selector if provided
                if video_selector:
                    video_elements = soup.select(video_selector)
                else:
                    # Default video element search
                    video_elements.extend(soup.find_all('video'))
                    video_elements.extend(soup.find_all('source', type=lambda x: x and 'video' in x))
                    video_elements.extend(soup.find_all('iframe', src=lambda x: x and ('youtube.com' in x or 'vimeo.com' in x)))
                    # Add more video element patterns
                    video_elements.extend(soup.find_all('a', href=lambda x: x and any(ext in x.lower() for ext in ['.mp4', '.webm', '.avi'])))
                    video_elements.extend(soup.find_all('div', class_=lambda x: x and 'video' in x.lower()))
                    
                    # 查找 script 标签中的视频 URL
                    scripts = soup.find_all('script')
                    for script in scripts:
                        if script.string:
                            # 查找常见的视频 URL 模式
                            video_urls = re.findall(r'https?://[^\s<>"]+?(?:\.mp4|\.webm|\.avi)[^\s<>"]*', script.string)
                            for url in video_urls:
                                video_elements.append({'src': url})
                
                # Extract URLs
                urls = []
                for element in video_elements:
                    if element.name == 'video':
                        src = element.get('src')
                        if src:
                            urls.append(src)
                    elif element.name == 'source':
                        src = element.get('src')
                        if src:
                            urls.append(src)
                    elif element.name == 'iframe':
                        src = element.get('src')
                        if src:
                            urls.append(src)
                    elif element.name == 'a':
                        href = element.get('href')
                        if href:
                            urls.append(href)
                    elif element.name == 'div':
                        # Try to find video URLs in data attributes
                        for attr in element.attrs:
                            if 'data' in attr and isinstance(element[attr], str):
                                if any(ext in element[attr].lower() for ext in ['.mp4', '.webm', '.avi']):
                                    urls.append(element[attr])
                    elif isinstance(element, dict) and 'src' in element:
                        urls.append(element['src'])
                
                return urls
            
            # Crawl pages with pagination
            all_videos = []
            current_page = start_page
            
            while current_page < start_page + max_pages:
                # Construct page URL
                if "?" in url:
                    page_url = f"{url}&{page_param}={current_page}"
                else:
                    page_url = f"{url}?{page_param}={current_page}"
                
                # Get page content
                html_content = await self.get_page_content(session, page_url, headers)
                if not html_content:
                    break
                
                # Parse videos from the page
                video_urls = parse_video_urls(html_content)
                if not video_urls:
                    break
                
                # Extract and download videos
                videos = await content_extractor.extract_videos(
                    html=html_content,
                    base_url=page_url,
                    save_dir=self.save_dir if download else None,
                    download=download,
                    video_types=self.supported_types,
                    max_size_mb=self.max_size_mb
                )
                
                # Log results
                logger.info(f"Found {len(videos)} videos on {page_url}")
                for video in videos:
                    logger.info(f"Video: {video['title'] or video['url']}")
                    if video['local_path']:
                        logger.info(f"Downloaded to: {video['local_path']}")
                
                all_videos.extend(videos)
                current_page += 1
                
                # 遵守请求延迟
                await asyncio.sleep(request_delay)
            
            return all_videos
            
        except Exception as e:
            logger.error(f"Error crawling videos: {e}")
            return []

async def run():
    """Run the video crawler."""
    # Initialize crawler
    crawler = VideoCrawler(
        save_dir="downloaded_videos",
        max_size_mb=500,
        supported_types=['.mp4', '.webm', '.avi']
    )
    
    # Example headers (customize as needed)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    # SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Example URLs (replace with actual URLs)
    urls = [
          "https://www.w3schools.com/html/html5_video.asp"  # 使用 W3Schools 的示例页面
    ]
    
    try:
        # Create a single session for all requests
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Crawl with pagination
            if urls:
                videos = await crawler.crawl_videos(
                    session=session,
                    url=urls[0],
                    download=True,
                    headers=headers,
                    request_delay=2.0,  # 增加延迟
                    start_page=1,
                    max_pages=3,  # 爬取3页
                    page_param="page",  # URL中的页码参数名
                    video_selector="video, source[type*=video], iframe[src*=player], a[href*='.mp4'], div[class*=video]"  # 视频元素选择器
                )
                
                print(f"\nFound {len(videos)} videos in total")
                for video in videos:
                    print(f"\nVideo: {video['title'] or video['url']}")
                    print(f"Type: {video['type']}")
                    print(f"Source: {video['source']}")
                    if video['local_path']:
                        print(f"Saved to: {video['local_path']}")
    
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
