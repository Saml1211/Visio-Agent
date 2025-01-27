from typing import List, Dict
from src.models.diagram import Diagram

class RelationshipDetector:
    """Detects relationships between shapes"""
    def __init__(self):
        self.relationship_rules = {
            "display": ["controller", "source"],
            "speaker": ["amplifier", "processor"]
        }
        
    def detect_relationships(self, diagram: Diagram) -> List[Dict]:
        """Detect relationships between shapes in a diagram"""
        relationships = []
        
        for shape in diagram.shapes:
            if shape.type in self.relationship_rules:
                for target_type in self.relationship_rules[shape.type]:
                    relationships.extend(
                        self._find_connections(shape, diagram, target_type)
                    )
                    
        return relationships
    
    def _find_connections(self, source, diagram, target_type):
        """Find connections between source and target type"""
        return [
            {
                "source": source.id,
                "target": target.id,
                "type": "connection"
            }
            for target in diagram.shapes
            if target.type == target_type
        ] 