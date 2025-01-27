import logging
from typing import Callable, Optional, Dict
import keyboard
import win32gui
import win32process
import psutil
from pathlib import Path
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)

class AppContext(Enum):
    """Enum representing different application contexts"""
    VISIO = auto()
    GENERAL = auto()

@dataclass
class HotkeyConfig:
    """Configuration for hotkey bindings"""
    activation_key: str = "ctrl+alt+q"  # Default hotkey
    always_on_top: bool = False
    minimize_to_tray: bool = True

class HotkeyService:
    """Service for managing global hotkeys and window focus detection"""
    
    def __init__(self, config: HotkeyConfig):
        """Initialize the hotkey service
        
        Args:
            config: Hotkey configuration
        """
        self.config = config
        self._callbacks: Dict[AppContext, Callable] = {}
        self._is_running = False
        logger.info(f"Initialized hotkey service with key: {config.activation_key}")
    
    def register_callback(self, context: AppContext, callback: Callable) -> None:
        """Register a callback for a specific application context
        
        Args:
            context: The application context (VISIO or GENERAL)
            callback: Function to call when hotkey is pressed in this context
        """
        self._callbacks[context] = callback
        logger.debug(f"Registered callback for context: {context}")
    
    def _get_active_window_process(self) -> Optional[str]:
        """Get the process name of the currently active window
        
        Returns:
            Process name or None if not found
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name().lower()
        except Exception as e:
            logger.error(f"Error getting active window process: {e}")
            return None
    
    def _hotkey_callback(self) -> None:
        """Handle hotkey press event"""
        try:
            process_name = self._get_active_window_process()
            
            if process_name == "visio.exe":
                logger.info("Visio context detected")
                if AppContext.VISIO in self._callbacks:
                    self._callbacks[AppContext.VISIO]()
            else:
                logger.info("General context detected")
                if AppContext.GENERAL in self._callbacks:
                    self._callbacks[AppContext.GENERAL]()
        except Exception as e:
            logger.error(f"Error in hotkey callback: {e}")
    
    def start(self) -> None:
        """Start listening for hotkey events"""
        if not self._is_running:
            try:
                keyboard.add_hotkey(
                    self.config.activation_key,
                    self._hotkey_callback,
                    suppress=True
                )
                self._is_running = True
                logger.info("Started hotkey service")
            except Exception as e:
                logger.error(f"Failed to start hotkey service: {e}")
                raise
    
    def stop(self) -> None:
        """Stop listening for hotkey events"""
        if self._is_running:
            try:
                keyboard.remove_hotkey(self.config.activation_key)
                self._is_running = False
                logger.info("Stopped hotkey service")
            except Exception as e:
                logger.error(f"Failed to stop hotkey service: {e}")
                raise
    
    @property
    def is_running(self) -> bool:
        """Check if the service is currently running"""
        return self._is_running 