"""
Spider module for web crawling.
"""
import re
from typing import Dict, Any, Optional, List, Callable
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from ..interfaces import ISpider
from .request_manager import RequestManager

class Spider(ISpider):
    """Spider implementation for web crawling."""
    
    def __init__(self, request_manager: RequestManager):
        """Initialize spider with request manager."""
        self.request_manager = request_manager
    
    async def crawl(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Crawl a webpage.
        
        Args:
            url: Target URL to crawl
            headers: Optional request headers
            
        Returns:
            Dictionary containing page content and metadata
            
        Raises:
            ValueError: If URL is invalid
            RequestError: If request fails
        """
        if not self.validate_url(url):
            raise ValueError(f"Invalid URL: {url}")
            
        try:
            html = await self.request_manager.make_request(url, headers=headers)
            timestamp = datetime.now().isoformat()
            
            return {
                'url': url,
                'html': html,
                'timestamp': timestamp,
                'parsed_data': await self.parse(html)
            }
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            raise
    
    async def crawl_with_pagination(
        self,
        base_url: str,
        page_parser: Callable[[str], List[str]],
        start_page: int = 1,
        max_pages: int = 1,
        page_param: str = "page"
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple pages with pagination.
        
        Args:
            base_url: Base URL to crawl
            page_parser: Function to parse URLs from page
            start_page: Starting page number
            max_pages: Maximum number of pages to crawl
            page_param: URL parameter for page number
            
        Returns:
            List of dictionaries containing page content and metadata
        """
        results = []
        current_page = start_page
        
        while current_page < start_page + max_pages:
            # Construct page URL
            if "?" in base_url:
                page_url = f"{base_url}&{page_param}={current_page}"
            else:
                page_url = f"{base_url}?{page_param}={current_page}"
                
            try:
                # Crawl current page
                page_content = await self.crawl(page_url)
                if not page_content:
                    break
                    
                # Parse URLs from current page
                urls = page_parser(page_content['html'])
                if not urls:
                    break
                    
                # Crawl individual URLs from current page
                for url in urls:
                    try:
                        content = await self.crawl(url)
                        if content:
                            results.append(content)
                    except Exception as e:
                        print(f"Error crawling {url}: {e}")
                        continue
                
                current_page += 1
                
            except Exception as e:
                print(f"Error crawling page {current_page}: {e}")
                break
                
        return results
    
    async def parse(self, html: str) -> Dict[str, Any]:
        """
        Parse HTML content and extract structured data.
        
        Args:
            html: HTML content to parse
            
        Returns:
            Dictionary containing parsed data
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract basic page information
        title = soup.title.string if soup.title else ""
        
        # Extract meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name', '')
            content = meta.get('content', '')
            if name and content:
                meta_tags[name] = content
                
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            links.append({
                'url': href,
                'text': text
            })
            
        return {
            'title': title,
            'meta_tags': meta_tags,
            'links': links[:100]  # Limit to first 100 links
        }

    def validate_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
