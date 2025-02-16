"""
Rate limiter for controlling request rates.
"""
import asyncio
from datetime import datetime
from typing import Dict
from ..interfaces import IRateLimiter

class RateLimiter(IRateLimiter):
    """Controls request rates per domain."""
    
    def __init__(self):
        self.rates = {}  # domain -> requests per second
        self.last_request = {}  # domain -> last request time
    
    async def acquire(self, domain: str) -> bool:
        """Check if request is allowed for domain."""
        if domain not in self.rates:
            return True
        
        now = datetime.now()
        if domain in self.last_request:
            time_diff = (now - self.last_request[domain]).total_seconds()
            if time_diff < 1.0 / self.rates[domain]:
                await asyncio.sleep(1.0 / self.rates[domain] - time_diff)
        
        self.last_request[domain] = now
        return True
    
    def update_rate(self, domain: str, requests_per_second: float) -> None:
        """Update rate limit for domain."""
        self.rates[domain] = requests_per_second
