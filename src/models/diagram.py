from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DiagramComponent(BaseModel):
    """Model for a diagram component."""
    id: str
    type: str
    x: float
    y: float
    properties: Dict[str, Any] = {}
    
class DiagramConnection(BaseModel):
    """Model for a connection between components."""
    id: str
    type: str
    from_id: str
    to_id: str
    properties: Dict[str, Any] = {}
    
class Diagram(BaseModel):
    """Model for a complete diagram."""
    id: str
    name: str
    components: List[DiagramComponent] = []
    connections: List[DiagramConnection] = []
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    metadata: Dict[str, Any] = {}
    
    def add_component(self, component: DiagramComponent) -> None:
        """Add a component to the diagram."""
        self.components.append(component)
        self.updated_at = datetime.now()
        
    def remove_component(self, component_id: str) -> None:
        """Remove a component from the diagram."""
        self.components = [c for c in self.components if c.id != component_id]
        # Remove any connections to/from this component
        self.connections = [
            c for c in self.connections 
            if c.from_id != component_id and c.to_id != component_id
        ]
        self.updated_at = datetime.now()
        
    def add_connection(self, connection: DiagramConnection) -> None:
        """Add a connection to the diagram."""
        self.connections.append(connection)
        self.updated_at = datetime.now()
        
    def remove_connection(self, connection_id: str) -> None:
        """Remove a connection from the diagram."""
        self.connections = [c for c in self.connections if c.id != connection_id]
        self.updated_at = datetime.now()
        
    def get_component(self, component_id: str) -> Optional[DiagramComponent]:
        """Get a component by ID."""
        for component in self.components:
            if component.id == component_id:
                return component
        return None
        
    def get_connection(self, connection_id: str) -> Optional[DiagramConnection]:
        """Get a connection by ID."""
        for connection in self.connections:
            if connection.id == connection_id:
                return connection
        return None
        
    def get_connected_components(self, component_id: str) -> List[DiagramComponent]:
        """Get all components connected to a given component."""
        connected_ids = set()
        for conn in self.connections:
            if conn.from_id == component_id:
                connected_ids.add(conn.to_id)
            elif conn.to_id == component_id:
                connected_ids.add(conn.from_id)
        
        return [c for c in self.components if c.id in connected_ids]
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the diagram to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'components': [c.dict() for c in self.components],
            'connections': [c.dict() for c in self.connections],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        } 