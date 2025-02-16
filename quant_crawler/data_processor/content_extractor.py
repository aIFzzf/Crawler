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
        video_types: List[str] = None,
        max_size_mb: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Extract video URLs and optionally download them.
        
        Args:
            html: HTML content to extract videos from
            base_url: Base URL for resolving relative paths
            save_dir: Directory to save downloaded videos
            download: Whether to download the videos
            video_types: List of video file extensions to extract (default: ['.mp4', '.webm', '.avi'])
            max_size_mb: Maximum video size in MB to download (default: 500MB)
            
        Returns:
            List of dictionaries containing video information:
            {
                'url': str,           # Original video URL
                'type': str,          # Video type/extension
                'source': str,        # Source element type (video, iframe, etc)
                'title': str,         # Video title if available
                'thumbnail': str,     # Thumbnail URL if available
                'local_path': str,    # Local path if downloaded
                'size': int,          # Size in bytes if available
                'duration': float,    # Duration in seconds if available
                'metadata': dict      # Additional metadata
            }
        """
        if video_types is None:
            video_types = ['.mp4', '.webm', '.avi']
            
        soup = BeautifulSoup(html, 'html.parser')
        videos = []
        
        # Create save directory if downloading
        if download and not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # Extract from video tags
        for video in soup.find_all('video'):
            for source in video.find_all('source'):
                video_info = await self._process_video_element(
                    source.get('src', ''),
                    base_url,
                    save_dir if download else None,
                    video_types,
                    max_size_mb,
                    {
                        'title': video.get('title', ''),
                        'poster': video.get('poster', ''),
                        'type': source.get('type', '')
                    }
                )
                if video_info:
                    videos.append(video_info)
                    
        # Extract from iframes (YouTube, Vimeo, etc)
        for iframe in soup.find_all('iframe'):
            video_info = await self._process_video_iframe(
                iframe.get('src', ''),
                base_url,
                save_dir if download else None,
                {
                    'title': iframe.get('title', ''),
                    'width': iframe.get('width', ''),
                    'height': iframe.get('height', '')
                }
            )
            if video_info:
                videos.append(video_info)
                
        # Extract direct video links from anchor tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(href.lower().endswith(ext) for ext in video_types):
                video_info = await self._process_video_element(
                    href,
                    base_url,
                    save_dir if download else None,
                    video_types,
                    max_size_mb,
                    {'title': link.get_text().strip()}
                )
                if video_info:
                    videos.append(video_info)
                    
        return videos
        
    async def _process_video_element(
        self,
        url: str,
        base_url: str,
        save_dir: str,
        video_types: List[str],
        max_size_mb: int,
        metadata: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Process a video element and optionally download it."""
        if not url:
            return None
            
        # Resolve relative URL
        url = urljoin(base_url, url)
        
        # Check if URL points to a video file
        if not any(url.lower().endswith(ext) for ext in video_types):
            return None
            
        video_info = {
            'url': url,
            'type': os.path.splitext(url)[1].lower(),
            'source': 'video',
            'title': metadata.get('title', ''),
            'thumbnail': metadata.get('poster', ''),
            'local_path': '',
            'size': 0,
            'duration': 0.0,
            'metadata': metadata
        }
        
        if save_dir:
            try:
                # Get video size before downloading
                async with aiohttp.ClientSession() as session:
                    async with session.head(url) as response:
                        size = int(response.headers.get('content-length', 0))
                        video_info['size'] = size
                        
                        if size > max_size_mb * 1024 * 1024:
                            logger.warning(f"Video size ({size/1024/1024:.1f}MB) exceeds limit ({max_size_mb}MB)")
                            return video_info
                        
                # Download video
                filename = self._get_safe_filename(metadata.get('title', '') or os.path.basename(url))
                local_path = os.path.join(save_dir, filename)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        with open(local_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                                
                video_info['local_path'] = local_path
                    
            except Exception as e:
                logger.error(f"Error downloading video {url}: {e}")
                
        return video_info
        
    async def _process_video_iframe(
        self,
        url: str,
        base_url: str,
        save_dir: str,
        metadata: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Process a video iframe (e.g., YouTube, Vimeo)."""
        if not url:
            return None
            
        # Resolve relative URL
        url = urljoin(base_url, url)
        
        # Extract video platform and ID
        platform_info = self._get_video_platform_info(url)
        if not platform_info:
            return None
            
        video_info = {
            'url': url,
            'type': platform_info['platform'],
            'source': 'iframe',
            'title': metadata.get('title', ''),
            'thumbnail': platform_info.get('thumbnail', ''),
            'local_path': '',
            'size': 0,
            'duration': 0.0,
            'metadata': {
                **metadata,
                'video_id': platform_info['id'],
                'embed_url': platform_info['embed_url']
            }
        }
        
        return video_info
        
    def _get_video_platform_info(self, url: str) -> Optional[Dict[str, str]]:
        """Get video platform information from URL."""
        # YouTube
        youtube_patterns = [
            r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/ ]{11})',
        ]
        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                return {
                    'platform': 'youtube',
                    'id': video_id,
                    'embed_url': f'https://www.youtube.com/embed/{video_id}',
                    'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
                }
                
        # Vimeo
        vimeo_patterns = [
            r'vimeo\.com/(?:video/)?(\d+)',
            r'player\.vimeo\.com/video/(\d+)'
        ]
        for pattern in vimeo_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                return {
                    'platform': 'vimeo',
                    'id': video_id,
                    'embed_url': f'https://player.vimeo.com/video/{video_id}',
                    'thumbnail': ''  # Vimeo requires API access for thumbnails
                }
                
        return None
        
    def _get_safe_filename(self, filename: str) -> str:
        """Convert string to safe filename."""
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip('. ')
        # Ensure filename is not empty
        if not filename:
            filename = 'video'
        return filename

    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
