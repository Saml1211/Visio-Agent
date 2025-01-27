from datetime import datetime, timedelta

class RateLimiter:
    """Implements rate limiting for fine-tuning requests"""
    def __init__(self, max_requests: int, period_hours: int):
        self.max_requests = max_requests
        self.period_hours = period_hours
        self.requests = []
        
    def can_request(self) -> bool:
        """Check if a new request is allowed"""
        self._clean_old_requests()
        return len(self.requests) < self.max_requests
        
    def record_request(self) -> None:
        """Record a new request"""
        self.requests.append(datetime.now())
        
    def _clean_old_requests(self) -> None:
        """Remove old requests from the history"""
        cutoff = datetime.now() - timedelta(hours=self.period_hours)
        self.requests = [req for req in self.requests if req > cutoff] 