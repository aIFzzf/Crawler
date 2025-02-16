"""
Core interfaces for the web crawler system.
This module defines the abstract base classes that form the foundation of the crawler system.
Each interface represents a specific component with well-defined responsibilities.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

class ISpider(ABC):
    """
    Interface for the spider component responsible for crawling web pages.
    Defines the core functionality needed for web crawling operations.
    """
    
    @abstractmethod
    async def crawl(self, url: str) -> Dict[str, Any]:
        """
        Crawl a specific URL and return the extracted data.
        
        Args:
            url (str): The target URL to crawl
            
        Returns:
            Dict[str, Any]: Dictionary containing crawled data
            
        Raises:
            ValueError: If URL is invalid
            RequestError: If request fails
        """
        pass
    
    @abstractmethod
    async def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse raw HTML content and extract structured data.
        
        Args:
            content (str): Raw HTML content to parse
            
        Returns:
            Dict[str, Any]: Structured data extracted from the content
        """
        pass
    
    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is properly formatted and crawlable.
        
        Args:
            url (str): URL to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        pass

class IRequestManager(ABC):
    """
    Interface for managing HTTP requests.
    Handles request creation, proxy settings, and retry policies.
    """
    
    @abstractmethod
    async def make_request(self, url: str, method: str = "GET", 
                          headers: Optional[Dict[str, str]] = None) -> str:
        """
        Make an HTTP request to the specified URL.
        
        Args:
            url (str): Target URL
            method (str, optional): HTTP method. Defaults to "GET"
            headers (Dict[str, str], optional): Request headers
            
        Returns:
            str: Response content
            
        Raises:
            RequestError: If request fails after all retries
        """
        pass
    
    @abstractmethod
    def set_proxy(self, proxy: str) -> None:
        """
        Set proxy for HTTP requests.
        
        Args:
            proxy (str): Proxy URL (e.g., "http://proxy.example.com:8080")
        """
        pass
    
    @abstractmethod
    def set_retry_policy(self, max_retries: int, delay: int) -> None:
        """
        Configure retry policy for failed requests.
        
        Args:
            max_retries (int): Maximum number of retry attempts
            delay (int): Delay between retries in seconds
        """
        pass

class IRateLimiter(ABC):
    """
    Interface for rate limiting requests.
    Controls request rates to avoid overwhelming servers.
    """
    
    @abstractmethod
    async def acquire(self, domain: str) -> bool:
        """
        Check if a request is allowed for the given domain.
        
        Args:
            domain (str): Target domain
            
        Returns:
            bool: True if request is allowed, False otherwise
        """
        pass
    
    @abstractmethod
    def update_rate(self, domain: str, requests_per_second: float) -> None:
        """
        Update rate limit for a domain.
        
        Args:
            domain (str): Target domain
            requests_per_second (float): Maximum requests per second
        """
        pass

class IContentExtractor(ABC):
    """
    Interface for content extraction.
    Handles extracting and processing HTML content.
    """
    
    @abstractmethod
    def extract_text(self, html: str) -> str:
        """
        Extract clean text from HTML content.
        
        Args:
            html (str): Raw HTML content
            
        Returns:
            str: Extracted text content
        """
        pass
    
    @abstractmethod
    def extract_structured_data(self, html: str) -> Dict[str, Any]:
        """
        Extract structured data from HTML.
        
        Args:
            html (str): Raw HTML content
            
        Returns:
            Dict[str, Any]: Structured data extracted from content
        """
        pass

class IDataClassifier(ABC):
    """
    Interface for data classification.
    Handles content categorization and labeling.
    """
    
    @abstractmethod
    def classify(self, content: str) -> str:
        """
        Classify content into predefined categories.
        
        Args:
            content (str): Content to classify
            
        Returns:
            str: Category label
        """
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """
        Get list of available categories.
        
        Returns:
            List[str]: List of category labels
        """
        pass
    
    @abstractmethod
    def train(self, training_data: List[Tuple[str, str]]) -> None:
        """
        Train classifier with labeled data.
        
        Args:
            training_data: List of (content, label) pairs
        """
        pass

class IDataStorage(ABC):
    """
    Interface for data storage.
    Handles storing and retrieving crawled data.
    """
    
    @abstractmethod
    async def save(self, data: Dict[str, Any], category: str) -> bool:
        """
        Save data to storage.
        
        Args:
            data (Dict[str, Any]): Data to save
            category (str): Category label for the data
            
        Returns:
            bool: True if save successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def retrieve(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve data from storage.
        
        Args:
            query (Dict[str, Any]): Query parameters for filtering data
            
        Returns:
            List[Dict[str, Any]]: List of matching data items
        """
        pass
    
    @abstractmethod
    async def update(self, query: Dict[str, Any], new_data: Dict[str, Any]) -> bool:
        """
        Update existing data.
        
        Args:
            query (Dict[str, Any]): Query to find data to update
            new_data (Dict[str, Any]): New data to apply
            
        Returns:
            bool: True if update successful, False otherwise
        """
        pass

class ITaskManager(ABC):
    """
    Interface for managing crawling tasks.
    Handles task queuing and scheduling.
    """
    
    @abstractmethod
    async def push_task(self, task: Dict[str, Any]) -> bool:
        """
        Add a new task to the queue.
        
        Args:
            task (Dict[str, Any]): Task configuration
            
        Returns:
            bool: True if task was queued successfully
        """
        pass
    
    @abstractmethod
    async def pop_task(self) -> Dict[str, Any]:
        """
        Get the next task from the queue.
        
        Returns:
            Dict[str, Any]: Next task configuration
            
        Raises:
            QueueEmpty: If queue is empty
        """
        pass
    
    @abstractmethod
    def schedule_task(self, task: Dict[str, Any], schedule_time: datetime) -> str:
        """
        Schedule a task for future execution.
        
        Args:
            task (Dict[str, Any]): Task configuration
            schedule_time (datetime): When to execute the task
            
        Returns:
            str: Task ID
        """
        pass

class IPerformanceMonitor(ABC):
    """
    Interface for performance monitoring.
    Tracks and analyzes system performance metrics.
    """
    
    @abstractmethod
    def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Record performance metrics.
        
        Args:
            metrics (Dict[str, Any]): Metrics to record
        """
        pass
    
    @abstractmethod
    def get_statistics(self, metric_name: str, time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Get statistics for a specific metric within a time range.
        
        Args:
            metric_name (str): Name of the metric to analyze
            time_range (Tuple[datetime, datetime]): Time range for analysis
            
        Returns:
            Dict[str, Any]: Dictionary containing metric statistics
        """
        pass

class IErrorHandler(ABC):
    """
    Interface for error handling.
    Manages error logging and tracking.
    """
    
    @abstractmethod
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Handle and log an error.
        
        Args:
            error (Exception): The error that occurred
            context (Dict[str, Any]): Additional context about the error
        """
        pass
    
    @abstractmethod
    def get_error_log(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Get error logs within a time range.
        
        Args:
            start_time (datetime): Start of time range
            end_time (datetime): End of time range
            
        Returns:
            List[Dict[str, Any]]: List of error entries within the time range
        """
        pass

class IMonitor(ABC):
    """
    Interface for system monitoring and error handling.
    Tracks performance metrics and handles errors.
    """
    
    @abstractmethod
    def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Record performance metrics.
        
        Args:
            metrics (Dict[str, Any]): Metrics to record
        """
        pass
    
    @abstractmethod
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Handle and log system errors.
        
        Args:
            error (Exception): The error that occurred
            context (Dict[str, Any]): Context information about the error
        """
        pass

class IDataProcessor(ABC):
    """
    Interface for processing and storing crawled data.
    Handles text extraction, classification, and data storage.
    """
    
    @abstractmethod
    def extract_text(self, html: str) -> str:
        """
        Extract clean text from HTML content.
        
        Args:
            html (str): Raw HTML content
            
        Returns:
            str: Extracted text content
        """
        pass
    
    @abstractmethod
    def classify(self, content: str) -> str:
        """
        Classify the content into predefined categories.
        
        Args:
            content (str): Text content to classify
            
        Returns:
            str: Category label
        """
        pass
    
    @abstractmethod
    async def save(self, data: Dict[str, Any], category: str) -> bool:
        """
        Save processed data to storage.
        
        Args:
            data (Dict[str, Any]): Processed data to save
            category (str): Category label for the data
            
        Returns:
            bool: True if save successful, False otherwise
        """
        pass
