"""
Request manager module for handling HTTP requests.
"""
import asyncio
from typing import Dict, Optional
import aiohttp
from loguru import logger
from ..interfaces import IRequestManager

class RequestManager(IRequestManager):
    """Request manager implementation."""
    
    def __init__(self, max_retries: int = 3, delay: int = 1):
        """Initialize request manager."""
        self.max_retries = max_retries
        self.delay = delay
        self._session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.proxy = None
    
    async def make_request(self, url: str, method: str = "GET", headers: Optional[Dict[str, str]] = None) -> str:
        """
        Make an HTTP request.
        
        Args:
            url: Target URL
            method: HTTP method (default: GET)
            headers: Optional request headers
            
        Returns:
            Response text if successful
            
        Raises:
            Exception: If request fails after all retries
        """
        try:
            if not self._session:
                self._session = aiohttp.ClientSession(headers=self.headers)
            
            merged_headers = self.headers.copy()
            if headers:
                merged_headers.update(headers)
                
            for attempt in range(self.max_retries):
                try:
                    async with self._session.request(method, url, headers=merged_headers, proxy=self.proxy) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.warning(f"Request failed with status {response.status}")
                            if attempt < self.max_retries - 1:
                                await asyncio.sleep(self.delay * (attempt + 1))
                            else:
                                response.raise_for_status()
                except aiohttp.ClientError as e:
                    logger.error(f"Request error: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.delay * (attempt + 1))
                    else:
                        raise
                        
            raise Exception(f"Failed to fetch {url} after {self.max_retries} attempts")
        except Exception as e:
            logger.error(f"Error making request to {url}: {e}")
            raise
    
    def set_proxy(self, proxy: str) -> None:
        """
        Set proxy for HTTP requests.
        
        Args:
            proxy: Proxy URL
        """
        self.proxy = proxy
    
    def set_retry_policy(self, max_retries: int, delay: int) -> None:
        """
        Configure retry policy for failed requests.
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.delay = delay
    
    async def close(self):
        """Close the session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
