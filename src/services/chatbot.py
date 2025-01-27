from enum import Enum, auto
from typing import Dict, List, Optional
from datetime import datetime
from src.services.rag_memory_service import RAGMemoryService
from src.services.self_learning_service import SelfLearningService

class ChatbotMode(Enum):
    """Enumeration of chatbot modes"""
    ACTION = auto()
    CHAT = auto()

class EnhancedChatbot:
    """Enhanced Q&A Chatbot with RAG integration, fine-tuning, and Action and Chat modes"""
    def __init__(self, rag_service: RAGMemoryService, learning_service: SelfLearningService, auto_mode_switch: bool = True):
        self.rag_service = rag_service
        self.learning_service = learning_service
        self.mode = ChatbotMode.CHAT
        self.auto_mode_switch = auto_mode_switch
        self.conversation_history = []
        
    async def handle_message(self, user_id: str, message: str) -> str:
        """Handle user message with auto mode switching"""
        if self.auto_mode_switch:
            self._auto_detect_mode(message)
            
        # Check for mode switching commands
        if message.startswith("/mode"):
            return self._handle_mode_command(message)
            
        # Process message based on current mode
        if self.mode == ChatbotMode.ACTION:
            return await self._handle_action_mode(user_id, message)
        else:
            return await self._handle_chat_mode(user_id, message)
            
    def _auto_detect_mode(self, message: str) -> None:
        """Automatically detect and switch mode based on message content"""
        action_keywords = ["generate", "create", "search", "execute", "run"]
        question_keywords = ["what", "how", "why", "explain", "describe"]
        
        if any(keyword in message.lower() for keyword in action_keywords):
            self.mode = ChatbotMode.ACTION
        elif any(keyword in message.lower() for keyword in question_keywords):
            self.mode = ChatbotMode.CHAT
            
    def _handle_mode_command(self, message: str) -> str:
        """Handle mode switching command"""
        mode = message[len("/mode"):].strip().lower()
        if mode in ["action", "action mode"]:
            self.mode = ChatbotMode.ACTION
            return "Switched to Action Mode"
        elif mode in ["chat", "chat mode"]:
            self.mode = ChatbotMode.CHAT
            return "Switched to Chat Mode"
        else:
            return f"Current mode: {self.mode.name}"
            
    async def _handle_action_mode(self, user_id: str, message: str) -> str:
        """Handle message in Action Mode"""
        try:
            # Parse and execute action
            action, params = self._parse_action(message)
            result = await self._execute_action(action, params)
            self._log_action(user_id, message, result)
            return result
        except Exception as e:
            return f"Action failed: {str(e)}"
            
    async def _handle_chat_mode(self, user_id: str, message: str) -> str:
        """Handle message in Chat Mode"""
        try:
            # Generate informative response
            response = await self._generate_response(message)
            self._log_conversation(user_id, message, response)
            return response
        except Exception as e:
            return f"Error generating response: {str(e)}"
            
    def _parse_action(self, message: str) -> tuple:
        """Enhanced action parsing with command recognition"""
        command_map = {
            "generate": self._parse_generate_command,
            "create": self._parse_create_command,
            "search": self._parse_search_command
        }
        
        for keyword, parser in command_map.items():
            if keyword in message.lower():
                return parser(message)
                
        return "default_action", {}
        
    def _parse_generate_command(self, message: str) -> tuple:
        """Parse generate commands"""
        if "report" in message.lower():
            return "generate_report", {"type": "BOM"}
        elif "diagram" in message.lower():
            return "generate_diagram", {"type": "Visio"}
        return "generate", {}
        
    def _parse_create_command(self, message: str) -> tuple:
        """Parse create commands"""
        if "document" in message.lower():
            return "create_document", {"type": "LLD"}
        return "create", {}
        
    def _parse_search_command(self, message: str) -> tuple:
        """Parse search commands"""
        query = message.lower().replace("search", "").strip()
        return "search", {"query": query}
        
    async def _execute_action(self, action: str, params: Dict) -> str:
        """Execute action based on parsed command"""
        # Implement action execution logic
        return f"Executed action: {action}"
        
    def _log_action(self, user_id: str, command: str, result: str) -> None:
        """Log action execution"""
        self.conversation_history.append({
            "user_id": user_id,
            "timestamp": datetime.now(),
            "type": "action",
            "command": command,
            "result": result
        })
        
    def _log_conversation(self, user_id: str, message: str, response: str) -> None:
        """Log conversation in Chat Mode"""
        self.conversation_history.append({
            "user_id": user_id,
            "timestamp": datetime.now(),
            "type": "chat",
            "message": message,
            "response": response
        })
        
    async def _handle_store_command(self, user_id: str, message: str) -> str:
        """Handle store to memory command"""
        try:
            # Extract content to store
            content = message[len("/store"):].strip()
            if not content:
                return "Please provide content to store"
                
            # Store in RAG memory
            await self.rag_service.store_memory(
                content=content,
                metadata={
                    "user_id": user_id,
                    "timestamp": datetime.now(),
                    "source": "chatbot"
                }
            )
            return "Content successfully stored in memory"
        except Exception as e:
            return f"Error storing content: {str(e)}"
            
    async def _handle_fine_tune_command(self, user_id: str, message: str) -> str:
        """Handle fine-tuning command"""
        try:
            # Get conversation history for fine-tuning
            training_data = self._prepare_training_data()
            if not training_data:
                return "No conversation history available for fine-tuning"
                
            # Initiate fine-tuning
            await self.learning_service.fine_tune_model(training_data)
            return "Model fine-tuning initiated successfully"
        except Exception as e:
            return f"Error during fine-tuning: {str(e)}"
            
    async def _handle_rag_command(self, user_id: str, message: str) -> str:
        """Handle RAG function call"""
        try:
            # Extract query
            query = message[len("/rag"):].strip()
            if not query:
                return "Please provide a search query"
                
            # Perform RAG search
            results = await self.rag_service.query_memory(query)
            return self._format_rag_results(results)
        except Exception as e:
            return f"Error performing RAG search: {str(e)}"
            
    def _prepare_training_data(self) -> List[Dict]:
        """Prepare conversation history for fine-tuning"""
        return [
            {
                "input": entry["message"],
                "output": entry["response"]
            }
            for entry in self.conversation_history
        ]
        
    def _format_rag_results(self, results: List[Dict]) -> str:
        """Format RAG search results for display"""
        if not results:
            return "No results found"
            
        return "\n".join(
            f"{i+1}. {result['content']}" 
            for i, result in enumerate(results[:5])
        )
        
    async def _handle_help_command(self, user_id: str) -> str:
        """Provide mode-specific help"""
        if self.mode == ChatbotMode.ACTION:
            return (
                "Action Mode Help:\n"
                "Available commands:\n"
                "- generate report\n"
                "- create document\n"
                "- search [query]\n"
                "Use /mode chat to switch to Chat Mode"
            )
        else:
            return (
                "Chat Mode Help:\n"
                "Ask questions about AV systems, LLDs, and the automation project.\n"
                "Use /mode action to switch to Action Mode"
            ) 