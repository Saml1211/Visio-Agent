import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
import psutil
import threading
import queue
import gc
from prometheus_client import Counter, Gauge, Histogram, start_http_server, Summary
import aiohttp
import asyncio

from .exceptions import PerformanceError

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """Configuration for monitoring service"""
    metrics_port: int = 8000
    performance_log: Path = Path("logs/performance.log")
    error_log: Path = Path("logs/error.log")
    health_check_interval: float = 60.0  # seconds
    memory_threshold: float = 0.9  # 90% of available memory
    cpu_threshold: float = 0.8  # 80% CPU usage
    response_time_threshold: float = 5.0  # seconds
    error_threshold: int = 10  # errors per minute
    max_error_history: int = 1000
    memory_growth_threshold: float = 0.1  # 10% growth between checks
    thread_idle_threshold: int = 300  # seconds
    alert_rate_limit: int = 60  # seconds between similar alerts
    slack_webhook: str = None
    email_config: Dict[str, Any] = None

class AlertDestination:
    """Base class for alert destinations"""
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        raise NotImplementedError

class SlackAlertDestination(AlertDestination):
    """Send alerts to Slack"""
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": f"*Alert*: {alert['message']}",
                    "attachments": [{
                        "fields": [
                            {"title": k, "value": str(v), "short": True}
                            for k, v in alert["data"].items()
                        ]
                    }]
                }
                async with session.post(self.webhook_url, json=payload) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False

class EmailAlertDestination(AlertDestination):
    """Send alerts via email"""
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
        
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        # Email alert implementation
        return True

class MonitoringService:
    """Service for monitoring application performance and health"""
    
    def __init__(self, config: MonitoringConfig):
        """Initialize monitoring service"""
        self.config = config
        self.config.performance_log.parent.mkdir(parents=True, exist_ok=True)
        self.config.error_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize Prometheus metrics
        self.request_counter = Counter(
            "chatbot_requests_total",
            "Total number of chatbot requests",
            ["type"]
        )
        
        self.response_time = Histogram(
            "chatbot_response_time_seconds",
            "Response time in seconds",
            ["type"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        self.memory_usage = Gauge(
            "chatbot_memory_usage_bytes",
            "Memory usage in bytes"
        )
        
        self.cpu_usage = Gauge(
            "chatbot_cpu_usage_percent",
            "CPU usage percentage"
        )
        
        self.error_counter = Counter(
            "chatbot_errors_total",
            "Total number of errors",
            ["type"]
        )
        
        self.thread_count = Gauge(
            "chatbot_thread_count",
            "Number of active threads"
        )
        
        self.memory_growth = Gauge(
            "chatbot_memory_growth_percent",
            "Memory growth percentage"
        )
        
        # New metrics
        self.validation_duration = Summary(
            "validation_duration_seconds",
            "Time spent on validation operations",
            ["validation_type"]
        )
        
        self.validation_errors = Counter(
            "validation_errors_total",
            "Total validation errors",
            ["error_type"]
        )
        
        self.resource_usage = Gauge(
            "resource_usage",
            "Resource usage metrics",
            ["resource_type"]
        )
        
        self.operation_queue_size = Gauge(
            "operation_queue_size",
            "Number of operations in queue",
            ["operation_type"]
        )
        
        self.alert_latency = Histogram(
            "alert_latency_seconds",
            "Time to process and send alerts",
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
        
        # Initialize alert destinations
        self.alert_destinations: List[AlertDestination] = []
        if self.config.slack_webhook:
            self.alert_destinations.append(
                SlackAlertDestination(self.config.slack_webhook)
            )
        if self.config.email_config:
            self.alert_destinations.append(
                EmailAlertDestination(self.config.email_config)
            )
        
        # Start Prometheus metrics server
        start_http_server(self.config.metrics_port)
        
        # Initialize performance tracking
        self._start_times: Dict[str, float] = {}
        self._operation_stats: Dict[str, Dict[str, float]] = {}
        
        # Initialize error tracking
        self._error_history: List[Dict[str, Any]] = []
        self._error_counts: Dict[str, int] = {}
        self._last_error_cleanup = time.time()
        
        # Initialize memory tracking
        self._last_memory_usage = psutil.Process().memory_percent()
        self._last_gc_collect = time.time()
        
        # Initialize thread tracking
        self._thread_history: Dict[int, float] = {}
        self._monitored_threads: Set[int] = set()
        
        # Health check thread
        self._stop_event = threading.Event()
        self._health_thread = threading.Thread(target=self._health_check_loop)
        self._health_thread.daemon = True
        
        # Alert queue and worker
        self.alert_queue = asyncio.Queue()
        self._alert_worker_task = None
        
        # Initialize alert rate limiting
        self._last_alerts: Dict[str, float] = {}
        
        # Initialize logging
        self._setup_logging()
        
        logger.info(
            f"Initialized monitoring service on port {self.config.metrics_port}"
        )
    
    def start(self) -> None:
        """Start monitoring service"""
        self._health_thread.start()
        self._alert_worker_task = asyncio.create_task(self._alert_worker())
        logger.info("Started monitoring service")
    
    def stop(self) -> None:
        """Stop monitoring service"""
        self._stop_event.set()
        self._health_thread.join(timeout=5)
        if self._alert_worker_task:
            self._alert_worker_task.cancel()
        logger.info("Stopped monitoring service")
    
    def start_operation(self, operation_id: str, operation_type: str) -> None:
        """Start tracking an operation
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation (e.g., "general_qa", "visio_command")
        """
        self._start_times[operation_id] = time.time()
        self.request_counter.labels(type=operation_type).inc()
    
    def end_operation(
        self,
        operation_id: str,
        operation_type: str,
        success: bool = True
    ) -> None:
        """End tracking an operation
        
        Args:
            operation_id: Unique identifier for the operation
            operation_type: Type of operation
            success: Whether the operation was successful
        """
        if operation_id in self._start_times:
            duration = time.time() - self._start_times[operation_id]
            self.response_time.labels(type=operation_type).observe(duration)
            
            # Update operation stats
            if operation_type not in self._operation_stats:
                self._operation_stats[operation_type] = {
                    "count": 0,
                    "total_time": 0,
                    "min_time": float("inf"),
                    "max_time": 0
                }
            
            stats = self._operation_stats[operation_type]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["min_time"] = min(stats["min_time"], duration)
            stats["max_time"] = max(stats["max_time"], duration)
            
            # Log performance data
            self._log_performance(operation_id, operation_type, duration, success)
            
            # Check for performance issues
            if duration > self.config.response_time_threshold:
                self._handle_performance_alert(
                    f"Slow operation detected: {operation_type}",
                    duration=duration,
                    threshold=self.config.response_time_threshold
                )
            
            del self._start_times[operation_id]
    
    def log_error(
        self,
        error_type: str,
        message: str,
        **context
    ) -> None:
        """Log an error with context
        
        Args:
            error_type: Type of error
            message: Error message
            **context: Additional error context
        """
        # Store timestamp as datetime object
        error_entry = {
            "type": error_type,
            "message": message,
            "timestamp": datetime.now(),  # Store as datetime
            "context": context
        }
        
        self._error_history.append(error_entry)
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        
        # Log to file
        with open(self.config.error_log, "a") as f:
            # Convert datetime to ISO format only when writing to file
            log_entry = {
                **error_entry,
                "timestamp": error_entry["timestamp"].isoformat()
            }
            f.write(json.dumps(log_entry) + "\n")
        
        # Check error rate
        self._check_error_rate(error_type)
    
    def _check_error_rate(self, error_type: str) -> None:
        """Check if error rate exceeds threshold"""
        now = datetime.now()
        
        # Cleanup old errors periodically
        if time.time() - self._last_error_cleanup > 60:
            cutoff = now - timedelta(minutes=1)
            self._error_history = [
                e for e in self._error_history 
                if e["timestamp"] > cutoff  # Direct datetime comparison
            ]
            self._last_error_cleanup = time.time()
        
        # Count recent errors - no parsing needed
        recent_errors = sum(
            1 for e in self._error_history
            if e["type"] == error_type and 
            e["timestamp"] > now - timedelta(minutes=1)
        )
        
        if recent_errors > self.config.error_threshold:
            self._handle_performance_alert(
                f"High error rate detected for {error_type}",
                error_type=error_type,
                error_count=recent_errors,
                threshold=self.config.error_threshold
            )
            
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics
        
        Returns:
            Dictionary containing error statistics
        """
        now = datetime.now()
        last_minute = now - timedelta(minutes=1)
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        def count_errors(since: datetime) -> Dict[str, int]:
            return {
                error_type: sum(
                    1 for e in self._error_history
                    if e["type"] == error_type and
                    e["timestamp"] > since
                )
                for error_type in set(e["type"] for e in self._error_history)
            }
            
        return {
            "total_counts": self._error_counts.copy(),
            "last_minute": count_errors(last_minute),
            "last_hour": count_errors(last_hour),
            "last_day": count_errors(last_day),
            "recent_errors": [
                e for e in self._error_history[-10:]
            ]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics
        
        Returns:
            Dictionary of performance statistics
        """
        stats = {
            "operations": self._operation_stats,
            "memory_usage": psutil.Process().memory_percent(),
            "cpu_usage": psutil.cpu_percent(),
            "error_counts": {
                name: self.error_counter.labels(type=name)._value.get()
                for name in self.error_counter._labelnames
            }
        }
        
        return stats
    
    def _check_memory_growth(self) -> None:
        """Check for potential memory leaks"""
        current_memory = psutil.Process().memory_percent()
        growth = (current_memory - self._last_memory_usage) / self._last_memory_usage
        
        self.memory_growth.set(growth * 100)
        
        if growth > self.config.memory_growth_threshold:
            # Potential memory leak detected
            if time.time() - self._last_gc_collect > 300:  # 5 minutes
                # Try garbage collection
                gc.collect()
                self._last_gc_collect = time.time()
                
                # Check if GC helped
                after_gc = psutil.Process().memory_percent()
                if (after_gc - self._last_memory_usage) / self._last_memory_usage > self.config.memory_growth_threshold:
                    self._handle_performance_alert(
                        "Potential memory leak detected",
                        growth_percent=growth * 100,
                        threshold=self.config.memory_growth_threshold * 100,
                        before_gc=current_memory,
                        after_gc=after_gc
                    )
        
        self._last_memory_usage = current_memory
    
    def _check_thread_health(self) -> None:
        """Check for potentially stuck threads"""
        current_time = time.time()
        current_threads = set()
        
        for thread in threading.enumerate():
            thread_id = thread.ident
            if thread_id:
                current_threads.add(thread_id)
                if thread_id not in self._thread_history:
                    self._thread_history[thread_id] = current_time
        
        # Check for idle threads
        for thread_id in list(self._thread_history.keys()):
            if thread_id not in current_threads:
                del self._thread_history[thread_id]
            elif current_time - self._thread_history[thread_id] > self.config.thread_idle_threshold:
                self._handle_performance_alert(
                    "Potentially stuck thread detected",
                    thread_id=thread_id,
                    idle_time=current_time - self._thread_history[thread_id],
                    threshold=self.config.thread_idle_threshold
                )
        
        self.thread_count.set(len(current_threads))
    
    def _health_check_loop(self) -> None:
        """Run periodic health checks"""
        while not self._stop_event.is_set():
            try:
                # Check memory usage
                memory_percent = psutil.Process().memory_percent()
                self.memory_usage.set(memory_percent)
                
                if memory_percent > self.config.memory_threshold:
                    self._handle_performance_alert(
                        "High memory usage detected",
                        actual=memory_percent,
                        threshold=self.config.memory_threshold
                    )
                
                # Check CPU usage
                cpu_percent = psutil.cpu_percent()
                self.cpu_usage.set(cpu_percent)
                
                if cpu_percent > self.config.cpu_threshold:
                    self._handle_performance_alert(
                        "High CPU usage detected",
                        actual=cpu_percent,
                        threshold=self.config.cpu_threshold
                    )
                
                # Check for memory leaks
                self._check_memory_growth()
                
                # Check thread health
                self._check_thread_health()
                
                # Sleep until next check
                time.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
    
    def _log_performance(
        self,
        operation_id: str,
        operation_type: str,
        duration: float,
        success: bool
    ) -> None:
        """Log performance data to file"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation_id": operation_id,
                "type": operation_type,
                "duration": duration,
                "success": success
            }
            
            with open(self.config.performance_log, "a") as f:
                json.dump(log_entry, f)
                f.write("\n")
                
        except Exception as e:
            logger.error(f"Error logging performance data: {e}")
    
    async def _alert_worker(self) -> None:
        """Process and send alerts asynchronously"""
        while True:
            try:
                alert = await self.alert_queue.get()
                start_time = time.time()
                
                # Send alert to all destinations
                results = await asyncio.gather(*[
                    dest.send_alert(alert)
                    for dest in self.alert_destinations
                ], return_exceptions=True)
                
                # Record alert latency
                self.alert_latency.observe(time.time() - start_time)
                
                # Log failures
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Alert destination {i} failed: {str(result)}"
                        )
                
                self.alert_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in alert worker: {str(e)}")
                await asyncio.sleep(1)
    
    async def _handle_performance_alert(
        self,
        message: str,
        **kwargs
    ) -> None:
        """Handle performance alerts
        
        Args:
            message: Alert message
            **kwargs: Additional alert data
        """
        try:
            # Check rate limit
            now = time.time()
            if message in self._last_alerts:
                time_since_last = now - self._last_alerts[message]
                if time_since_last < self.config.alert_rate_limit:
                    logger.debug(
                        f"Suppressing alert due to rate limit: {message}"
                    )
                    return
            
            alert = {
                "timestamp": datetime.now().isoformat(),
                "message": message,
                "data": kwargs,
                "severity": kwargs.get("severity", "warning")
            }
            
            # Add to queue for async processing
            await self.alert_queue.put(alert)
            
            # Log alert
            logger.warning(f"Performance alert: {message}")
            
            # Update last alert time
            self._last_alerts[message] = now
            
            # Clean up old alerts
            cutoff = now - self.config.alert_rate_limit * 2
            self._last_alerts = {
                msg: ts for msg, ts in self._last_alerts.items()
                if ts > cutoff
            }
            
        except Exception as e:
            logger.error(f"Error handling performance alert: {e}")
    
    def get_alerts(self, max_alerts: Optional[int] = None) -> list:
        """Get pending alerts
        
        Args:
            max_alerts: Maximum number of alerts to return
            
        Returns:
            List of alert dictionaries
        """
        alerts = []
        try:
            while not self.alert_queue.empty():
                if max_alerts and len(alerts) >= max_alerts:
                    break
                alerts.append(self.alert_queue.get_nowait())
        except queue.Empty:
            pass
        
        return alerts
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics
        
        Returns:
            Dictionary containing alert statistics including:
            - alert_counts: Count of each type of alert
            - rate_limited: Number of rate-limited alerts
            - active_alerts: Currently active alerts
        """
        now = time.time()
        stats = {
            "alert_counts": {},
            "rate_limited": 0,
            "active_alerts": []
        }
        
        # Count alerts in queue
        alerts = []
        while not self.alert_queue.empty():
            try:
                alert = self.alert_queue.get_nowait()
                alerts.append(alert)
                
                # Update counts
                message = alert["message"]
                stats["alert_counts"][message] = stats["alert_counts"].get(message, 0) + 1
                
                # Check if still active
                if now - datetime.fromisoformat(alert["timestamp"]).timestamp() < self.config.alert_rate_limit:
                    stats["active_alerts"].append(alert)
                
            except queue.Empty:
                break
        
        # Put alerts back in queue
        for alert in alerts:
            self.alert_queue.put(alert)
        
        # Count rate-limited alerts
        stats["rate_limited"] = sum(
            1 for ts in self._last_alerts.values()
            if now - ts < self.config.alert_rate_limit
        )
        
        return stats