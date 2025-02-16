"""
Logging configuration for the crawler.
"""
import os
import sys
from datetime import datetime
from loguru import logger

def setup_logging(name: str = "quant_crawler") -> None:
    """
    Set up logging configuration.
    
    Args:
        name: Name prefix for log files
    """
    # Remove default handler
    logger.remove()
    
    # Get log directory
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    
    # Add handlers
    # Console handler - INFO level
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # File handler - DEBUG level
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="100 MB",  # Rotate when file reaches 100MB
        retention="30 days"  # Keep logs for 30 days
    )
    
    logger.info(f"Logging configured. Log file: {log_file}")
