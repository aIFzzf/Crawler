"""
Basic usage example of crawler.

This example demonstrates how to use the basic features of crawler
to crawl a website and extract data, images and videos.
"""

import os
import asyncio
from crawler.crawler_core import Spider, RequestManager, RateLimiter
from crawler.data_processor import ContentExtractor, DataStorage, VideoExtractor
from crawler.monitor import PerformanceMonitor

async def crawl_images(spider, content_extractor, url, save_dir):
    """Crawl and save images from the given URL."""
    content = await spider.crawl(url)
    images = await content_extractor.extract_images(
        html=content['html'],
        base_url=url,
        save_dir=save_dir,
        download=True
    )
    return images

async def crawl_text(spider, content_extractor, url):
    """Crawl and extract text content from the given URL."""
    content = await spider.crawl(url)
    text = content_extractor.extract_text(content['html'])
    structured_data = content_extractor.extract_structured_data(content['html'])
    return {
        'text': text,
        'structured_data': structured_data
    }

async def crawl_videos(spider, video_extractor, url, save_dir):
    """Crawl and save videos from the given URL."""
    content = await spider.crawl(url)
    videos = await video_extractor.extract_videos(
        html=content['html'],
        base_url=url,
        save_dir=save_dir,
        download=True
    )
    return videos

async def main():
    # Initialize components
    request_manager = RequestManager()
    spider = Spider(request_manager)
    content_extractor = ContentExtractor()
    video_extractor = VideoExtractor()
    data_storage = DataStorage()
    
    # Set request headers
    request_manager.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,video/webm,*/*;q=0.8',
    }
    
    # Set rate limit
    rate_limiter = RateLimiter()
    rate_limiter.update_rate('example.com', 1.0)  # 1 request per second
    
    try:
        # Create save directories
        base_dir = os.path.join(os.getcwd(), 'downloaded_content')
        images_dir = os.path.join(base_dir, 'images')
        videos_dir = os.path.join(base_dir, 'videos')
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(videos_dir, exist_ok=True)

        # URLs to crawl (replace with your target URLs)
        urls = [
            'https://example.com/page1',
            'https://example.com/page2',
            'https://example.com/page3'
        ]

        # Crawl all URLs concurrently
        for url in urls:
            print(f"\nCrawling {url}...")
            
            # Crawl images, text, and videos concurrently
            tasks = [
                crawl_images(spider, content_extractor, url, images_dir),
                crawl_text(spider, content_extractor, url),
                crawl_videos(spider, video_extractor, url, videos_dir)
            ]
            
            images, text_data, videos = await asyncio.gather(*tasks)
            
            # Print results
            print(f"\nResults for {url}:")
            print(f"- Found {len(images)} images")
            print(f"- Extracted {len(text_data['text'].split())} words")
            print(f"- Found {len(videos)} videos")
            
            # Save data
            await data_storage.save({
                'url': url,
                'text': text_data['text'],
                'structured_data': text_data['structured_data'],
                'images': [img.to_dict() for img in images],
                'videos': [video.to_dict() for video in videos]
            }, f'example_{url.split("/")[-1]}')
            
        print("\nSuccessfully crawled and saved all content")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await request_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
