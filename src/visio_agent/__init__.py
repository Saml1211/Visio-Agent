"""
Visio Agent - AI-powered system for automating AV system diagrams
"""

from .api.main import app
from .config.settings import Settings
from .services.service_registry import ServiceRegistry

__version__ = "1.0.0"
__all__ = ["app", "Settings", "ServiceRegistry"] 