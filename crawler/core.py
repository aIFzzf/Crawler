"""
Core implementation of the web crawler system.
This module provides concrete implementations of the interfaces defined in interfaces.py.
Each class implements specific functionality while maintaining loose coupling.
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from .interfaces import (
    ISpider,
    IRequestManager,
    IDataProcessor,
    ITaskManager,
    IMonitor
)
from .crawler_core.content_analyzer import ContentAnalyzer

class RequestManager(IRequestManager):
    """
    Handles HTTP requests with support for proxies, retry mechanisms and cookies.
    Uses aiohttp for asynchronous HTTP requests.
    """
    
    def __init__(self):
        """Initialize RequestManager with default settings."""
        self.session = aiohttp.ClientSession()
        self.proxy = None
        self.max_retries = 3
        self.delay = 1
        
    async def make_request(self, url: str, method: str = "GET",
                          headers: Optional[Dict[str, str]] = None, cookies: Optional[Dict[str, str]] = None) -> str:
        """
        Make HTTP request with automatic retry on failure.
        
        Args:
            url: Target URL
            method: HTTP method (default: "GET")
            headers: Optional request headers
            cookies: Optional request cookies
            
        Returns:
            str: Response content
            
        Raises:
            Exception: If all retry attempts fail
        """
        for attempt in range(self.max_retries):
            try:
                async with self.session.request(
                    method, url, headers=headers, cookies=cookies, proxy=self.proxy
                ) as response:
                    return await response.text()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                await asyncio.sleep(self.delay * (attempt + 1))
    
    def set_proxy(self, proxy: str) -> None:
        """Set proxy for HTTP requests."""
        self.proxy = proxy
    
    def set_retry_policy(self, max_retries: int, delay: int) -> None:
        """Configure retry policy for failed requests."""
        self.max_retries = max_retries
        self.delay = delay

    async def close(self):
        """Close the session."""
        if self.session:
            await self.session.close()
            self.session = None

class Spider(ISpider):
    """
    Core spider implementation for crawling web pages.
    """
    
    def __init__(self, request_manager: IRequestManager):
        """Initialize spider with request manager."""
        self.request_manager = request_manager
        self.content_analyzer = ContentAnalyzer()
    
    async def crawl(self, url: str) -> Dict[str, Any]:
        """
        Crawl a URL and return parsed data.
        
        Args:
            url: Target URL to crawl
            
        Returns:
            Dict containing parsed data
        """
        try:
            content = await self.request_manager.make_request(url, headers=self.headers)
            return await self.parse(content)
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            raise
    
    async def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse HTML content and extract data.
        
        Args:
            content: HTML content to parse
            
        Returns:
            Dict containing parsed data
        """
        try:
            soup = BeautifulSoup(content, 'lxml')
            
            # Extract list items
            list_items = []
            for item in soup.select('.item'):  # Adjust selector based on actual HTML
                item_data = {
                    'text': item.get_text(strip=True),
                    'links': [a.get('href') for a in item.select('a[href]')],
                    'html': str(item)
                }
                list_items.append(item_data)
            
            # Extract pagination info
            pagination = {
                'current_page': self._extract_current_page(soup),
                'total_pages': self._extract_total_pages(soup),
                'next_page': self._extract_next_page(soup)
            }
            
            return {
                'list_items': list_items,
                'pagination': pagination,
                'raw_html': content
            }
        except Exception as e:
            logger.error(f"Error parsing content: {str(e)}")
            return {'list_items': [], 'pagination': {}, 'raw_html': content}
    
    def _extract_current_page(self, soup: BeautifulSoup) -> int:
        """Extract current page number."""
        try:
            page_elem = soup.select_one('.current-page')  # Adjust selector
            return int(page_elem.text) if page_elem else 1
        except:
            return 1
    
    def _extract_total_pages(self, soup: BeautifulSoup) -> int:
        """Extract total number of pages."""
        try:
            total_elem = soup.select_one('.total-pages')  # Adjust selector
            return int(total_elem.text) if total_elem else 1
        except:
            return 1
    
    def _extract_next_page(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract next page URL."""
        try:
            next_link = soup.select_one('.next-page')  # Adjust selector
            return next_link.get('href') if next_link else None
        except:
            return None

class DataProcessor(IDataProcessor):
    """
    Processes and stores crawled data.
    Handles text extraction, classification, and storage.
    """
    
    def extract_text(self, html: str) -> str:
        """Extract clean text from HTML using BeautifulSoup."""
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    
    def classify(self, content: str) -> str:
        """
        Classify content into categories.
        Currently returns a default category - extend for custom classification.
        """
        return "general"
    
    async def save(self, data: Dict[str, Any], category: str) -> bool:
        """
        Save processed data.
        Currently logs the save operation - extend for actual storage implementation.
        """
        logger.info(f"Saving data to category: {category}")
        return True

class TaskManager(ITaskManager):
    """
    Manages crawling tasks using asyncio.Queue.
    Handles task queuing and scheduling.
    """
    
    def __init__(self):
        """Initialize TaskManager with empty queue and task storage."""
        self.queue = asyncio.Queue()
        self.scheduled_tasks = {}
    
    async def push_task(self, task: Dict[str, Any]) -> bool:
        """Add task to queue."""
        await self.queue.put(task)
        return True
    
    async def pop_task(self) -> Dict[str, Any]:
        """Get next task from queue."""
        return await self.queue.get()
    
    def schedule_task(self, task: Dict[str, Any], schedule_time: datetime) -> str:
        """
        Schedule task for future execution.
        
        Returns:
            str: Task ID for tracking
        """
        task_id = str(len(self.scheduled_tasks))
        self.scheduled_tasks[task_id] = (task, schedule_time)
        return task_id

class Monitor(IMonitor):
    """
    System monitoring and error handling.
    Uses loguru for logging metrics and errors.
    """
    
    def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """Log performance metrics."""
        logger.info(f"Recording metrics: {metrics}")
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Log errors with context information."""
        logger.error(f"Error occurred: {error}, Context: {context}")
