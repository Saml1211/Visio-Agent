from typing import Dict, Any, Optional
from pydantic import BaseModel
import asyncio
from datetime import datetime

class SharedState(BaseModel):
    """Shared state model for managing application state."""
    user_id: Optional[str] = None
    tool_states: Dict[str, Dict[str, Any]] = {}
    
    async def get_tool_state(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get the state for a specific tool."""
        return self.tool_states.get(tool_name)
    
    async def update_tool_state(self, tool_name: str, state: Dict[str, Any]) -> None:
        """Update the state for a specific tool."""
        self.tool_states[tool_name] = state
    
    def update(self, data: Dict[str, Any]) -> None:
        """Update the shared state with new data."""
        for key, value in data.items():
            if key == "tool_states":
                self.tool_states.update(value)
            elif hasattr(self, key):
                setattr(self, key, value)

class SharedStateOld(BaseModel):
    """Shared state for the application."""
    
    # Active sessions and their data
    sessions: Dict[str, Dict[str, Any]] = {}
    
    # Active tools and their states
    tool_states: Dict[str, Dict[str, Any]] = {}
    
    # Global application state
    global_state: Dict[str, Any] = {
        "active_users": 0,
        "last_update": None,
        "system_status": "ready"
    }
    
    # Locks for thread safety
    _locks: Dict[str, asyncio.Lock] = {}
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        super().__init__(**data)
        self._locks = {
            "sessions": asyncio.Lock(),
            "tool_states": asyncio.Lock(),
            "global_state": asyncio.Lock()
        }
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Update session data."""
        async with self._locks["sessions"]:
            if session_id not in self.sessions:
                self.sessions[session_id] = {}
            self.sessions[session_id].update(data)
            self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        async with self._locks["sessions"]:
            return self.sessions.get(session_id)
    
    async def update_global_state(self, state: Dict[str, Any]) -> None:
        """Update global state."""
        async with self._locks["global_state"]:
            self.global_state.update(state)
            self.global_state["last_update"] = datetime.now().isoformat()
    
    async def get_global_state(self) -> Dict[str, Any]:
        """Get global state."""
        async with self._locks["global_state"]:
            return self.global_state.copy()
    
    async def increment_active_users(self) -> int:
        """Increment active users count."""
        async with self._locks["global_state"]:
            self.global_state["active_users"] += 1
            return self.global_state["active_users"]
    
    async def decrement_active_users(self) -> int:
        """Decrement active users count."""
        async with self._locks["global_state"]:
            self.global_state["active_users"] = max(0, self.global_state["active_users"] - 1)
            return self.global_state["active_users"]
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> None:
        """Clean up old sessions."""
        async with self._locks["sessions"]:
            now = datetime.now()
            to_remove = []
            for session_id, data in self.sessions.items():
                last_activity = datetime.fromisoformat(data["last_activity"])
                if (now - last_activity).total_seconds() > max_age_hours * 3600:
                    to_remove.append(session_id)
            for session_id in to_remove:
                del self.sessions[session_id] 