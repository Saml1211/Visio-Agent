import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
from typing import Callable, Optional
from pathlib import Path
import json
import pyperclip
import logging
from dataclasses import dataclass
import threading
import queue

logger = logging.getLogger(__name__)

@dataclass
class ChatbotUIConfig:
    """Configuration for the chatbot UI"""
    window_title: str = "AI Assistant"
    window_width: int = 600
    window_height: int = 400
    font_family: str = "Arial"
    font_size: int = 10
    theme_file: Optional[Path] = None
    opacity: float = 0.95
    max_history: int = 1000  # Maximum number of messages to keep

class ChatbotWindow:
    """Main window for the chatbot UI"""
    
    def __init__(
        self,
        config: ChatbotUIConfig,
        on_submit: Callable[[str], None],
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """Initialize the chatbot window"""
        self.config = config
        self.on_submit = on_submit
        self.loop = loop or asyncio.get_event_loop()
        
        # Message queue for thread-safe UI updates
        self.message_queue = queue.Queue()
        
        # Create main window
        self.root = tk.Tk()
        self.root.title(config.window_title)
        self.root.geometry(f"{config.window_width}x{config.window_height}")
        
        # Set window attributes
        self.root.attributes("-alpha", config.opacity)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Thread-safe state variables
        self._is_processing = threading.Event()
        self._is_minimized = threading.Event()
        
        # Load theme if specified
        if config.theme_file and config.theme_file.exists():
            self._load_theme(config.theme_file)
        
        self._create_widgets()
        self._setup_bindings()
        
        # Start message processing
        self._start_message_processing()
        
        # Initially minimized
        self.minimize()
        
        logger.info("Initialized chatbot window")
    
    def _create_widgets(self) -> None:
        """Create and arrange UI widgets"""
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create output text area
        self.output_text = scrolledtext.ScrolledText(
            self.main_frame,
            wrap=tk.WORD,
            font=(self.config.font_family, self.config.font_size)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.output_text.config(state=tk.DISABLED)
        
        # Create input frame
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Create input text box
        self.input_text = ttk.Entry(input_frame)
        self.input_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create submit button
        self.submit_button = ttk.Button(
            input_frame,
            text="Submit",
            command=self._handle_submit
        )
        self.submit_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Create copy button
        self.copy_button = ttk.Button(
            input_frame,
            text="Copy",
            command=self._copy_to_clipboard
        )
        self.copy_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Create clear button
        self.clear_button = ttk.Button(
            input_frame,
            text="Clear",
            command=self._clear_output
        )
        self.clear_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Create always on top checkbox
        self.always_on_top_var = tk.BooleanVar(value=False)
        self.always_on_top_check = ttk.Checkbutton(
            self.main_frame,
            text="Always on Top",
            variable=self.always_on_top_var,
            command=self._toggle_always_on_top
        )
        self.always_on_top_check.pack(anchor=tk.W)
        
        # Create status label
        self.status_label = ttk.Label(self.main_frame, text="Ready")
        self.status_label.pack(anchor=tk.W)
    
    def _setup_bindings(self) -> None:
        """Set up keyboard bindings"""
        self.input_text.bind("<Return>", lambda e: self._handle_submit())
        self.root.bind("<Escape>", lambda e: self.minimize())
        self.root.bind("<Control-c>", lambda e: self._copy_to_clipboard())
        self.root.bind("<Control-l>", lambda e: self._clear_output())
    
    def _start_message_processing(self) -> None:
        """Start processing messages from queue"""
        def process_messages():
            try:
                while True:
                    try:
                        message = self.message_queue.get_nowait()
                        self._update_output_text(message)
                    except queue.Empty:
                        break
                self.root.after(100, process_messages)
            except Exception as e:
                logger.error(f"Error processing messages: {e}")
                self.root.after(100, process_messages)
        
        self.root.after(100, process_messages)
    
    def _update_output_text(self, message: str) -> None:
        """Update output text in a thread-safe way"""
        try:
            self.output_text.config(state=tk.NORMAL)
            self.output_text.insert(tk.END, message + "\n\n")
            
            # Limit history size
            content = self.output_text.get("1.0", tk.END)
            lines = content.split("\n")
            if len(lines) > self.config.max_history:
                self.output_text.delete("1.0", f"{len(lines) - self.config.max_history}.0")
            
            self.output_text.see(tk.END)
            self.output_text.config(state=tk.DISABLED)
        except Exception as e:
            logger.error(f"Error updating output text: {e}")
    
    def _handle_submit(self) -> None:
        """Handle submit button click or Enter key"""
        if self._is_processing.is_set():
            return
        
        query = self.input_text.get().strip()
        if query:
            self._is_processing.set()
            self.status_label.config(text="Processing...")
            self.input_text.delete(0, tk.END)
            self.message_queue.put("You: " + query)
            
            # Call the callback in the event loop
            asyncio.run_coroutine_threadsafe(
                self._async_handle_submit(query),
                self.loop
            )
    
    async def _async_handle_submit(self, query: str) -> None:
        """Handle submit asynchronously"""
        try:
            await self.on_submit(query)
        except Exception as e:
            logger.error(f"Error handling submit: {e}")
            self.message_queue.put(f"Error: {str(e)}")
        finally:
            self._is_processing.clear()
            self.status_label.config(text="Ready")
    
    def add_message(self, message: str) -> None:
        """Add a message to the output text area"""
        self.message_queue.put(message)
    
    def _copy_to_clipboard(self) -> None:
        """Copy selected text to clipboard"""
        try:
            selected_text = self.output_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            pyperclip.copy(selected_text)
            self.status_label.config(text="Copied to clipboard")
            self.root.after(2000, lambda: self.status_label.config(text="Ready"))
        except tk.TclError:  # No selection
            pass
    
    def _clear_output(self) -> None:
        """Clear output text area"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.status_label.config(text="Output cleared")
        self.root.after(2000, lambda: self.status_label.config(text="Ready"))
    
    def _toggle_always_on_top(self) -> None:
        """Toggle always on top state"""
        self.root.attributes("-topmost", self.always_on_top_var.get())
    
    def _load_theme(self, theme_file: Path) -> None:
        """Load custom theme from JSON file"""
        try:
            with open(theme_file) as f:
                theme = json.load(f)
            
            style = ttk.Style()
            style.theme_create("custom", parent="alt", settings=theme)
            style.theme_use("custom")
        except Exception as e:
            logger.error(f"Error loading theme: {e}")
    
    def minimize(self) -> None:
        """Minimize the window"""
        self._is_minimized.set()
        self.root.iconify()
    
    def restore(self) -> None:
        """Restore the window from minimized state"""
        self._is_minimized.clear()
        self.root.deiconify()
        self.root.lift()
        self.input_text.focus()
    
    def _on_close(self) -> None:
        """Handle window close event"""
        self.minimize()
    
    def start(self) -> None:
        """Start the UI event loop"""
        try:
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in UI event loop: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the UI"""
        try:
            self.root.quit()
        except Exception as e:
            logger.error(f"Error stopping UI: {e}")
            raise