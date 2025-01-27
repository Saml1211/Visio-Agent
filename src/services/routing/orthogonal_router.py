import networkx as nx
from typing import List, Tuple

class OrthogonalRouter:
    def __init__(self, grid_size: float):
        self.grid_size = grid_size
        
    def calculate_route(self, start: Tuple[float, float], 
                      end: Tuple[float, float],
                      obstacles: List[Tuple[float, float, float, float]]) -> List[Tuple[float, float]]:
        """Calculate orthogonal path with obstacle avoidance"""
        grid = self._create_grid(start, end, obstacles)
        path = nx.astar_path(grid, self._snap_to_grid(start), self._snap_to_grid(end))
        return self._optimize_path(path) 