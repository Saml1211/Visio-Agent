from typing import Literal
from pydantic import BaseModel
from enum import Enum

class ConnectorConfig(BaseModel):
    routing_style: Literal["straight", "orthogonal", "curved"] = "orthogonal"
    spacing_mm: float = 5.0
    avoid_shapes: bool = True
    optimization_level: Literal["none", "basic", "aggressive"] = "basic"
    corner_radius: float = 2.0  # For orthogonal
    curve_tension: float = 0.5   # For curved 

class ConnectorStyle(str, Enum):
    ORTHOGONAL = "orthogonal"
    CURVED = "curved"
    STRAIGHT = "straight"

class RoutingConfig(BaseModel):
    default_style: ConnectorStyle = ConnectorStyle.ORTHOGONAL
    grid_spacing: float = 5.0  # in mm
    shape_padding: float = 2.0
    optimize_crossings: bool = True
    curve_smoothness: float = 0.5 