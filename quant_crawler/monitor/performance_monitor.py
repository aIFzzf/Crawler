"""
Performance monitoring implementation.
"""
from typing import Dict, Any, Tuple
from datetime import datetime
import json
import aiofiles
from loguru import logger
from ..interfaces import IPerformanceMonitor

class PerformanceMonitor(IPerformanceMonitor):
    """
    Monitors and records system performance metrics.
    Implements performance tracking and statistics calculation.
    """
    
    def __init__(self, metrics_file: str = "metrics.json"):
        """
        Initialize performance monitor.
        
        Args:
            metrics_file: File path for storing metrics
        """
        self.metrics_file = metrics_file
        self.current_metrics = {}
    
    def record_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Record performance metrics.
        
        Args:
            metrics: Dictionary containing metrics to record
        """
        timestamp = datetime.now().isoformat()
        self.current_metrics[timestamp] = metrics
        self._save_metrics()
    
    def get_statistics(self, metric_name: str, time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Get statistics for a specific metric within a time range.
        
        Args:
            metric_name: Name of the metric to analyze
            time_range: Tuple of (start_time, end_time)
            
        Returns:
            Dictionary containing metric statistics
        """
        start_time, end_time = time_range
        relevant_metrics = []
        
        for timestamp, metrics in self.current_metrics.items():
            metric_time = datetime.fromisoformat(timestamp)
            if start_time <= metric_time <= end_time and metric_name in metrics:
                relevant_metrics.append(metrics[metric_name])
        
        if not relevant_metrics:
            return {}
        
        return {
            'count': len(relevant_metrics),
            'average': sum(relevant_metrics) / len(relevant_metrics),
            'min': min(relevant_metrics),
            'max': max(relevant_metrics)
        }
    
    async def _save_metrics(self) -> None:
        """Save metrics to file."""
        try:
            async with aiofiles.open(self.metrics_file, 'w') as f:
                await f.write(json.dumps(self.current_metrics, indent=2))
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
