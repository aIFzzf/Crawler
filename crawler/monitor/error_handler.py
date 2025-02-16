"""
Error handling implementation.
"""
from typing import Dict, Any, List
from datetime import datetime
import json
import aiofiles
from loguru import logger
from ..interfaces import IErrorHandler

class ErrorHandler(IErrorHandler):
    """
    Handles and logs system errors.
    Implements error tracking and logging functionality.
    """
    
    def __init__(self, error_log_file: str = "error_log.json"):
        """
        Initialize error handler.
        
        Args:
            error_log_file: File path for storing error logs
        """
        self.error_log_file = error_log_file
        self.errors = []
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Handle and log an error.
        
        Args:
            error: The error that occurred
            context: Additional context about the error
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            'context': context
        }
        
        # Log error
        logger.error(f"Error: {error_entry['error_type']} - {error_entry['error_message']}")
        logger.error(f"Context: {context}")
        
        # Store error
        self.errors.append(error_entry)
        self._save_errors()
    
    def get_error_log(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Get error logs within a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of error entries within the specified time range
        """
        return [
            error for error in self.errors
            if start_time <= datetime.fromisoformat(error['timestamp']) <= end_time
        ]
    
    async def _save_errors(self) -> None:
        """Save errors to file."""
        try:
            async with aiofiles.open(self.error_log_file, 'w') as f:
                await f.write(json.dumps(self.errors, indent=2))
        except Exception as e:
            logger.error(f"Error saving error log: {e}")
