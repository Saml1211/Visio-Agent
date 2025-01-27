from typing import List, Dict, Optional
from datetime import datetime, timedelta

class ConversationManager:
    """Manages conversation history with pruning and search capabilities"""
    def __init__(self, max_history_days: int = 30, max_entries: int = 1000):
        self.max_history_days = max_history_days
        self.max_entries = max_entries
        self.conversations = []
        
    def add_conversation(self, user_id: str, message: str, response: str) -> None:
        """Add a new conversation entry"""
        self.conversations.append({
            "user_id": user_id,
            "timestamp": datetime.now(),
            "message": message,
            "response": response
        })
        self._prune_old_entries()
        
    def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversations for a user"""
        return [
            conv for conv in self.conversations
            if conv["user_id"] == user_id
        ][-limit:]
        
    def search_conversations(self, query: str, user_id: Optional[str] = None) -> List[Dict]:
        """Search conversations by content"""
        return [
            conv for conv in self.conversations
            if query.lower() in conv["message"].lower() or
               query.lower() in conv["response"].lower()
            and (user_id is None or conv["user_id"] == user_id)
        ]
        
    def _prune_old_entries(self) -> None:
        """Prune old conversation entries"""
        cutoff = datetime.now() - timedelta(days=self.max_history_days)
        self.conversations = [
            conv for conv in self.conversations
            if conv["timestamp"] > cutoff
        ][-self.max_entries:] 