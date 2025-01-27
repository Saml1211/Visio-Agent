from pydantic import BaseModel
from typing import Dict, List, Optional

class ShapeConfig(BaseModel):
    """Configuration for Visio shapes"""
    id: str
    type: str
    position: Dict[str, float]
    size: Dict[str, float]
    style: Dict[str, str]
    text: Optional[str] = None

class ConnectorConfig(BaseModel):
    """Configuration for Visio connectors"""
    id: str
    source_id: str
    target_id: str
    routing_style: str
    points: List[Dict[str, float]]
    style: Dict[str, str] 