"""
Content extraction implementation.
"""
import os
import aiohttp
import aiofiles
from typing import Dict, Any, List, Optional, Union
from bs4 import BeautifulSoup
from loguru import logger
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin, urlparse
from ..interfaces import IContentExtractor
import re

class ImageInfo:
    """
    Class to store image information.
    """
    def __init__(self, url: str, alt: str = "", width: Optional[int] = None, 
                 height: Optional[int] = None, file_path: Optional[str] = None):
        self.url = url
        self.alt = alt
        self.width = width
        self.height = height
        self.file_path = file_path

    def to_dict(self) -> Dict[str, Any]:
        """Convert image info to dictionary."""
        return {
            "url": self.url,
            "alt": self.alt,
            "width": self.width,
            "height": self.height,
            "file_path": self.file_path
        }

class ContentExtractor(IContentExtractor):
    """
    Extracts and processes content from HTML.
    """
    
    def __init__(self):
        """Initialize the content extractor."""
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if not hasattr(self, '_session') or not self._session:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the session if it exists."""
        if hasattr(self, '_session') and self._session:
            await self._session.close()
            self._session = None

    async def extract_text(self, html: str) -> str:
        """
        Extract clean text from HTML content.
        
        Args:
            html: HTML content
            
        Returns:
            Cleaned text content
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for script in soup(['script', 'style']):
            script.decompose()
            
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        return text

    async def extract_images(self, html: str, base_url: str, save_dir: Optional[str] = None,
                           download: bool = False) -> List[ImageInfo]:
        """
        Extract image information from HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative URLs
            save_dir: Directory to save downloaded images
            download: Whether to download the images
            
        Returns:
            List of ImageInfo objects
        """
        soup = BeautifulSoup(html, 'lxml')
        images = []
        
        # Create save directory if needed
        if download and save_dir:
            os.makedirs(save_dir, exist_ok=True)
        
        # Get session for downloading
        session = await self._get_session()
        
        for img in soup.find_all('img'):
            try:
                # Get image URL
                src = img.get('src', '')
                if not src:
                    continue
                
                # Handle relative URLs
                if not urlparse(src).netloc:
                    src = urljoin(base_url, src)
                
                # Create ImageInfo object
                image_info = ImageInfo(
                    url=src,
                    alt=img.get('alt', ''),
                    width=int(img.get('width', 0)) or None,
                    height=int(img.get('height', 0)) or None
                )
                
                if download and save_dir:
                    try:
                        # Download image
                        async with session.get(src) as response:
                            if response.status == 200:
                                content = await response.read()
                                
                                # Get image dimensions if not provided
                                if not image_info.width or not image_info.height:
                                    with Image.open(BytesIO(content)) as img:
                                        image_info.width, image_info.height = img.size
                                
                                # Generate filename
                                filename = os.path.join(
                                    save_dir,
                                    f"image_{len(images)}_{os.path.basename(urlparse(src).path)}"
                                )
                                
                                # Save image
                                async with aiofiles.open(filename, 'wb') as f:
                                    await f.write(content)
                                
                                image_info.file_path = filename
                                logger.info(f"Downloaded image: {filename}")
                            else:
                                logger.warning(f"Failed to download image {src}: {response.status}")
                    
                    except Exception as e:
                        logger.error(f"Error downloading image {src}: {e}")
                
                images.append(image_info)
            
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                continue
        
        return images
    
    async def extract_structured_data(self, html: str) -> Dict[str, Any]:
        """
        Extract structured data from HTML content.
        
        Args:
            html: HTML content
            
        Returns:
            Dictionary containing structured data
        """
        soup = BeautifulSoup(html, 'lxml')
        data = {
            "title": soup.title.string if soup.title else "",
            "meta_description": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "",
            "meta_keywords": soup.find("meta", {"name": "keywords"})["content"] if soup.find("meta", {"name": "keywords"}) else "",
            "headings": {
                "h1": [h.get_text(strip=True) for h in soup.find_all("h1")],
                "h2": [h.get_text(strip=True) for h in soup.find_all("h2")],
                "h3": [h.get_text(strip=True) for h in soup.find_all("h3")]
            }
        }
        return data
    
    async def extract_videos(
        self,
        html: str,
        base_url: str,
        save_dir: str = "videos",
        download: bool = False,
        video_types: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract video URLs and optionally download them.
        
        Args:
            html: HTML content to extract videos from
            base_url: Base URL for resolving relative paths
            save_dir: Directory to save downloaded videos
            download: Whether to download the videos
            video_types: List of video file extensions to extract (default: ['.mp4', '.webm', '.ogg'])
            
        Returns:
            List of dictionaries containing video information:
            {
                'url': str,           # Original video URL
                'type': str,          # Video type/extension
                'source': str,        # Source element type (video, iframe, etc)
                'title': str,         # Video title if available
                'metadata': dict      # Additional metadata
            }
        """
        if video_types is None:
            video_types = ['.mp4', '.webm', '.ogg']
            
        soup = BeautifulSoup(html, 'html.parser')
        videos = []
        
        # Extract from video tags
        for video in soup.find_all('video'):
            # Check for src attribute first
            src = video.get('src')
            if src:
                abs_url = urljoin(base_url, src)
                video_info = {
                    'url': abs_url,
                    'type': os.path.splitext(src)[1].lower(),
                    'source': 'video',
                    'title': video.get('title', ''),
                    'metadata': {
                        'width': video.get('width', ''),
                        'height': video.get('height', ''),
                        'controls': video.has_attr('controls')
                    }
                }
                videos.append(video_info)
                continue
                
            # Check for source tags
            for source in video.find_all('source'):
                src = source.get('src')
                if src:
                    abs_url = urljoin(base_url, src)
                    video_info = {
                        'url': abs_url,
                        'type': os.path.splitext(src)[1].lower(),
                        'source': 'video',
                        'title': video.get('title', ''),
                        'metadata': {
                            'width': video.get('width', ''),
                            'height': video.get('height', ''),
                            'controls': video.has_attr('controls'),
                            'type': source.get('type', '')
                        }
                    }
                    videos.append(video_info)
                    
        if download and videos:
            os.makedirs(save_dir, exist_ok=True)
            for video in videos:
                filename = os.path.join(save_dir, os.path.basename(video['url']))
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(video['url']) as response:
                            if response.status == 200:
                                with open(filename, 'wb') as f:
                                    f.write(await response.read())
                                video['local_path'] = filename
                except Exception as e:
                    logger.error(f"Failed to download video {video['url']}: {str(e)}")
                    
        return videos

    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
