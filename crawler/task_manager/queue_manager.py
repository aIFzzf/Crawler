"""
Queue manager for handling crawling tasks.
"""
import asyncio
from typing import Dict, Any
from ..interfaces import IQueueManager

class QueueManager(IQueueManager):
    """Manages task queue operations."""
    
    def __init__(self):
        self.queue = asyncio.Queue()
        self.active_tasks = {}
    
    async def push_task(self, task: Dict[str, Any]) -> bool:
        """Add task to queue."""
        try:
            await self.queue.put(task)
            self.active_tasks[id(task)] = task
            return True
        except Exception:
            return False
    
    async def pop_task(self) -> Dict[str, Any]:
        """Get next task from queue."""
        task = await self.queue.get()
        if id(task) in self.active_tasks:
            del self.active_tasks[id(task)]
        return task
    
    def get_queue_status(self) -> Dict:
        """Get current queue status."""
        return {
            'queue_size': self.queue.qsize(),
            'active_tasks': len(self.active_tasks)
        }
