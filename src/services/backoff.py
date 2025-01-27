import random
from typing import Optional

class ExponentialBackoff:
    """Implements exponential backoff with jitter for retries"""
    
    def __init__(
        self,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        factor: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize backoff parameters
        
        Args:
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            factor: Multiplication factor for exponential increase
            jitter: Whether to add random jitter
        """
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.factor = factor
        self.jitter = jitter
        
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number
        
        Args:
            attempt: The attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.factor ** (attempt - 1)),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter between 0-25% of the delay
            jitter = random.uniform(0, 0.25 * delay)
            delay += jitter
            
        return delay 