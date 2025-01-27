import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import json
import time
import asyncio
from datetime import datetime

from .ai_service_config import AIServiceManager
from .rag_memory_service import RAGMemoryService
from .visio_generation_service import VisioGenerationService
from .llm_ai_service import LLMBasedAIService
from .exceptions import ChatbotError, ServiceError, RateLimitError
from ..utils.retry import with_retry

logger = logging.getLogger(__name__)

@dataclass
class ChatbotConfig:
    """Configuration for the chatbot service"""
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    log_file: Path = Path("logs/chatbot.log")
    performance_log: Path = Path("logs/performance.log")
    system_config: Path = Path("config/chatbot_config.json")
    retry_attempts: int = 3
    retry_delay: float = 1.0
    context_window: int = 5  # Number of previous interactions to include

class ChatbotService:
    """Service for handling both general Q&A and Visio-specific interactions"""
    
    def __init__(
        self,
        config: ChatbotConfig,
        ai_service: AIServiceManager,
        rag_memory: RAGMemoryService,
        visio_service: Optional[VisioGenerationService] = None
    ):
        """Initialize the chatbot service"""
        self.config = config
        self.ai_service = ai_service
        self.rag_memory = rag_memory
        self.visio_service = visio_service
        
        # Create log directories
        self.config.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.config.performance_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Load system configuration
        self.system_config = self._load_system_config()
        
        # Initialize conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        logger.info("Initialized chatbot service")
    
    def _load_system_config(self) -> Dict[str, Any]:
        """Load system configuration from JSON file"""
        try:
            if self.config.system_config.exists():
                with open(self.config.system_config) as f:
                    return json.load(f)
            else:
                logger.warning("System config not found, using defaults")
                return {}
        except Exception as e:
            logger.error(f"Error loading system config: {e}")
            return {}
    
    def _update_conversation_history(self, role: str, content: str) -> None:
        """Update conversation history with new message"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.conversation_history) > self.config.context_window:
            self.conversation_history = self.conversation_history[-self.config.context_window:]
    
    def _format_conversation_context(self) -> str:
        """Format conversation history for context"""
        context = "Previous conversation:\n"
        for msg in self.conversation_history:
            context += f"{msg['role']}: {msg['content']}\n"
        return context
    
    async def _log_performance(self, context: str, start_time: float, success: bool) -> None:
        """Log performance metrics"""
        duration = time.time() - start_time
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "timestamp": timestamp,
            "context": context,
            "duration": duration,
            "success": success,
            "model": self.config.model_name
        }
        
        try:
            with open(self.config.performance_log, "a") as f:
                json.dump(log_entry, f)
                f.write("\n")
        except Exception as e:
            logger.error(f"Error logging performance: {e}")
    
    @with_retry(retries=3, delay=1.0)
    async def handle_general_query(self, query: str) -> str:
        """Handle a general Q&A query"""
        start_time = time.time()
        success = False
        
        try:
            # Get relevant context from RAG memory
            context = await self.rag_memory.query_memory(query)
            
            # Get conversation history
            conv_context = self._format_conversation_context()
            
            # Prepare prompt with context
            prompt = f"""Context from knowledge base:
            {context}
            
            {conv_context}
            
            Current question: {query}
            
            Please provide a helpful and accurate response."""
            
            # Get AI response
            response = await self.ai_service.generate_text(
                prompt,
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            # Update conversation history
            self._update_conversation_history("user", query)
            self._update_conversation_history("assistant", response)
            
            # Store interaction in RAG memory
            await self.rag_memory.add_interaction(query, response)
            
            success = True
            return response
            
        except Exception as e:
            logger.error(f"Error handling general query: {e}")
            raise ChatbotError(f"Failed to process query: {str(e)}")
        
        finally:
            await self._log_performance("general_qa", start_time, success)
    
    @with_retry(retries=3, delay=1.0)
    async def handle_visio_command(self, command: str) -> str:
        """Handle a Visio-specific command"""
        if not self.visio_service:
            raise ChatbotError("Visio service not initialized")
        
        start_time = time.time()
        success = False
        
        try:
            # Get relevant context from RAG memory
            context = await self.rag_memory.query_memory(command)
            
            # Get conversation history
            conv_context = self._format_conversation_context()
            
            # Prepare prompt for Visio command interpretation
            prompt = f"""Context from previous Visio operations:
            {context}
            
            {conv_context}
            
            Current Visio command: {command}
            
            Please interpret this command and provide the necessary Visio API actions in JSON format.
            Include specific function calls and parameters required."""
            
            # Get AI interpretation of command
            interpretation = await self.ai_service.generate_text(
                prompt,
                model=self.config.model_name,
                temperature=self.config.temperature
            )
            
            try:
                # Parse the interpretation as JSON
                actions = json.loads(interpretation)
                
                # Execute Visio actions
                # This is where you would implement the actual Visio API calls
                # based on the interpreted actions
                
                response = "Command processed successfully"
                
            except json.JSONDecodeError:
                raise ChatbotError("Failed to parse Visio command interpretation")
            
            # Update conversation history
            self._update_conversation_history("user", command)
            self._update_conversation_history("assistant", response)
            
            # Store interaction in RAG memory
            await self.rag_memory.add_interaction(command, response)
            
            success = True
            return response
            
        except Exception as e:
            logger.error(f"Error handling Visio command: {e}")
            raise ChatbotError(f"Failed to process Visio command: {str(e)}")
        
        finally:
            await self._log_performance("visio_command", start_time, success)