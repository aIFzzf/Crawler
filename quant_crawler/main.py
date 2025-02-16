"""
Main entry point for the web crawler system.
This module provides the CrawlerSystem class that integrates all components
and provides a high-level interface for crawling operations.
"""
import asyncio
from datetime import datetime, timedelta
from typing import List
from loguru import logger

from .core import (
    RequestManager,
    Spider,
    DataProcessor,
    TaskManager,
    Monitor
)

class CrawlerSystem:
    """
    Main crawler system that integrates all components.
    Provides high-level interface for crawling operations.
    """
    
    def __init__(self):
        """Initialize crawler system with all required components."""
        self.request_manager = RequestManager()
        self.spider = Spider(self.request_manager)
        self.data_processor = DataProcessor()
        self.task_manager = TaskManager()
        self.monitor = Monitor()
    
    async def crawl_url(self, url: str) -> bool:
        """
        Crawl a single URL and process its content.
        
        Args:
            url (str): Target URL to crawl
            
        Returns:
            bool: True if crawl was successful, False otherwise
            
        This method:
        1. Crawls the specified URL
        2. Extracts and processes the content
        3. Classifies the content
        4. Saves the processed data
        5. Records performance metrics
        """
        try:
            # Record start time for metrics
            start_time = datetime.now()
            
            # Crawl the URL
            data = await self.spider.crawl(url)
            
            # Process the data
            text = self.data_processor.extract_text(data['text'])
            category = self.data_processor.classify(text)
            
            # Save the processed data
            await self.data_processor.save(
                {
                    'url': url,
                    'content': text,
                    'category': category,
                    'metadata': {
                        'crawl_time': start_time.isoformat(),
                        'title': data.get('title', ''),
                        'links': data.get('links', [])
                    }
                },
                category
            )
            
            # Record metrics
            end_time = datetime.now()
            self.monitor.record_metrics({
                'url': url,
                'crawl_time': (end_time - start_time).total_seconds(),
                'success': True
            })
            
            return True
            
        except Exception as e:
            self.monitor.handle_error(e, {'url': url})
            return False
    
    async def process_queue(self):
        """
        Continuously process tasks from the queue.
        This method runs indefinitely until interrupted.
        
        The processing loop:
        1. Gets next task from queue
        2. Processes the task
        3. Handles any errors
        4. Implements rate limiting through sleep
        """
        while True:
            try:
                task = await self.task_manager.pop_task()
                url = task['url']
                await self.crawl_url(url)
            except Exception as e:
                self.monitor.handle_error(e, {'task': task})
            await asyncio.sleep(1)  # Prevent CPU overuse
    
    async def start(self, urls: List[str]):
        """
        Start the crawler system with a list of URLs.
        
        Args:
            urls (List[str]): List of URLs to crawl
            
        This method:
        1. Schedules all URLs as tasks
        2. Starts the queue processing loop
        """
        # Schedule tasks
        for url in urls:
            await self.task_manager.push_task({'url': url})
        
        # Start processing queue
        await self.process_queue()

async def main():
    """
    Example usage of the crawler system.
    
    This function:
    1. Creates a crawler instance
    2. Defines target URLs
    3. Starts the crawling process
    4. Handles interruption and errors
    """
    # Example usage
    crawler = CrawlerSystem()
    urls = [
        'https://example.com',
        'https://example.org'
    ]
    
    try:
        await crawler.start(urls)
    except KeyboardInterrupt:
        logger.info("Crawler stopped by user")
    except Exception as e:
        logger.error(f"Crawler stopped due to error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
