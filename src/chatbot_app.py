import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json
import sys
import threading
from queue import Queue
import signal
import atexit
import traceback
from datetime import datetime

from .services.hotkey_service import HotkeyService, HotkeyConfig, AppContext
from .services.chatbot_service import ChatbotService, ChatbotConfig
from .services.ai_service_config import AIServiceManager
from .services.rag_memory_service import RAGMemoryService
from .services.visio_generation_service import VisioGenerationService
from .ui.chatbot_window import ChatbotWindow, ChatbotUIConfig
from .services.exceptions import ServiceError

logger = logging.getLogger(__name__)

class ChatbotApp:
    """Main application class integrating all chatbot components"""
    
    def __init__(self, config_file: Path):
        """Initialize the chatbot application"""
        self.config_file = config_file
        self.shutdown_event = threading.Event()
        self.threads = []
        
        try:
            # Load configuration
            self.config = self._load_config(config_file)
            
            # Set up logging
            self._setup_logging()
            
            # Register shutdown handlers
            self._register_shutdown_handlers()
            
            # Create event loop
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Initialize services
            self._init_services()
            
            # Message queue for thread communication
            self.message_queue = Queue()
            
            logger.info("Initialized chatbot application")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            self._log_error(e)
            sys.exit(1)
    
    def _init_services(self) -> None:
        """Initialize all required services"""
        try:
            # Initialize AI service
            self.ai_service = AIServiceManager(self.config["ai_service"])
            
            # Initialize RAG memory
            self.rag_memory = RAGMemoryService(self.config["rag_memory"])
            
            # Initialize Visio service if configured
            self.visio_service = None
            if "visio_service" in self.config:
                self.visio_service = VisioGenerationService(
                    ai_service_manager=self.ai_service,
                    rag_memory=self.rag_memory,
                    **self.config["visio_service"]
                )
            
            # Initialize chatbot service
            self.chatbot_service = ChatbotService(
                ChatbotConfig(**self.config["chatbot"]),
                self.ai_service,
                self.rag_memory,
                self.visio_service
            )
            
            # Initialize UI
            self.ui = ChatbotWindow(
                ChatbotUIConfig(**self.config["ui"]),
                self._handle_user_input,
                self.loop
            )
            
            # Initialize hotkey service
            self.hotkey_service = HotkeyService(
                HotkeyConfig(**self.config["hotkey"])
            )
            
            # Register hotkey callbacks
            self.hotkey_service.register_callback(
                AppContext.GENERAL,
                self._handle_general_hotkey
            )
            self.hotkey_service.register_callback(
                AppContext.VISIO,
                self._handle_visio_hotkey
            )
            
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            self._log_error(e)
            raise
    
    def _load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load and validate configuration"""
        try:
            with open(config_file) as f:
                config = json.load(f)
            
            # Validate required sections
            required_sections = ["ai_service", "rag_memory", "chatbot", "ui", "hotkey", "logging"]
            missing = [s for s in required_sections if s not in config]
            if missing:
                raise ValueError(f"Missing required config sections: {missing}")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def _setup_logging(self) -> None:
        """Set up logging configuration"""
        try:
            log_config = self.config.get("logging", {})
            log_file = log_config.get("file")
            
            if log_file:
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logging.basicConfig(
                level=log_config.get("level", "INFO"),
                format=log_config.get(
                    "format",
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
                filename=log_file,
                filemode="a"
            )
            
            # Add console handler if not logging to file
            if not log_file:
                console = logging.StreamHandler()
                console.setLevel(logging.INFO)
                formatter = logging.Formatter(log_config.get(
                    "format",
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ))
                console.setFormatter(formatter)
                logging.getLogger("").addHandler(console)
            
        except Exception as e:
            print(f"Error setting up logging: {e}")  # Can't use logger yet
            raise
    
    def _register_shutdown_handlers(self) -> None:
        """Register handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        atexit.register(self.stop)
    
    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.stop()
    
    def _log_error(self, error: Exception) -> None:
        """Log detailed error information"""
        try:
            error_log = Path(self.config["logging"].get("error_file", "logs/errors.log"))
            error_log.parent.mkdir(parents=True, exist_ok=True)
            
            with open(error_log, "a") as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Error: {str(error)}\n")
                f.write("Traceback:\n")
                f.write(traceback.format_exc())
                f.write(f"{'='*50}\n")
                
        except Exception as e:
            logger.error(f"Failed to log error details: {e}")
    
    def _handle_general_hotkey(self) -> None:
        """Handle hotkey press in general context"""
        try:
            self.ui.restore()
        except Exception as e:
            logger.error(f"Error handling general hotkey: {e}")
            self._log_error(e)
    
    def _handle_visio_hotkey(self) -> None:
        """Handle hotkey press in Visio context"""
        try:
            if self.visio_service:
                self.ui.restore()
                self.ui.add_message("Visio mode activated")
        except Exception as e:
            logger.error(f"Error handling Visio hotkey: {e}")
            self._log_error(e)
    
    async def _handle_user_input(self, query: str) -> None:
        """Handle user input from UI"""
        try:
            if self.hotkey_service._get_active_window_process() == "visio.exe":
                response = await self.chatbot_service.handle_visio_command(query)
            else:
                response = await self.chatbot_service.handle_general_query(query)
            
            self.ui.add_message("Assistant: " + response)
            
        except ServiceError as e:
            logger.error(f"Service error handling input: {e}")
            self.ui.add_message(f"Service error: {str(e)}")
            self._log_error(e)
            
        except Exception as e:
            logger.error(f"Error handling user input: {e}")
            self.ui.add_message(f"Error: {str(e)}")
            self._log_error(e)
    
    def _run_ui(self) -> None:
        """Run the UI in a separate thread"""
        try:
            self.ui.start()
        except Exception as e:
            logger.error(f"Error in UI thread: {e}")
            self._log_error(e)
            self.message_queue.put(("error", str(e)))
    
    def _run_async_loop(self) -> None:
        """Run the async event loop in a separate thread"""
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"Error in async loop: {e}")
            self._log_error(e)
            self.message_queue.put(("error", str(e)))
    
    def start(self) -> None:
        """Start the application"""
        try:
            # Start hotkey service
            self.hotkey_service.start()
            
            # Start UI thread
            ui_thread = threading.Thread(target=self._run_ui)
            ui_thread.daemon = True
            ui_thread.start()
            self.threads.append(ui_thread)
            
            # Start async loop thread
            loop_thread = threading.Thread(target=self._run_async_loop)
            loop_thread.daemon = True
            loop_thread.start()
            self.threads.append(loop_thread)
            
            logger.info("Started chatbot application")
            
            # Monitor message queue
            while not self.shutdown_event.is_set():
                try:
                    msg_type, msg_data = self.message_queue.get(timeout=1)
                    if msg_type == "error":
                        logger.error(f"Error from thread: {msg_data}")
                        break
                except Queue.Empty:
                    continue
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            self._log_error(e)
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the application"""
        if self.shutdown_event.is_set():
            return
        
        logger.info("Stopping chatbot application")
        self.shutdown_event.set()
        
        try:
            # Stop services in reverse order
            self.hotkey_service.stop()
            self.ui.stop()
            
            # Stop event loop
            if self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            # Wait for threads to finish
            for thread in self.threads:
                thread.join(timeout=5)
            
            logger.info("Stopped chatbot application")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
            self._log_error(e)
            sys.exit(1)