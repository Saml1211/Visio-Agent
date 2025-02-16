from typing import Dict, Any, Optional
import asyncio
from pydantic import BaseModel

class SharedState(BaseModel):
    """Shared application state."""
    
    tool_states: Dict[str, Dict[str, Any]] = {}
    active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def get_tool_state(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get state for a specific tool."""
        return self.tool_states.get(tool_name)
    
    async def update_tool_state(self, tool_name: str, state: Dict[str, Any]) -> None:
        """Update state for a specific tool."""
        self.tool_states[tool_name] = state
    
    async def create_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Create a new session."""
        self.active_sessions[session_id] = data 