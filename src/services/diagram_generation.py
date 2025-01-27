from typing import List, Dict
from src.services.shape_classifier import ShapeClassifierService
from src.models.diagram import Diagram

class DiagramGenerationService:
    def __init__(self, shape_classifier: ShapeClassifierService):
        self.shape_classifier = shape_classifier
        
    def generate_diagram(self, components: List[Dict]) -> Diagram:
        """Generate diagram with classified shapes"""
        diagram = Diagram()
        
        for component in components:
            shape_type = self.shape_classifier.classify_shape(component["image"])
            diagram.add_shape(
                shape_type=shape_type["class_name"],
                position=component["position"],
                metadata=component["metadata"]
            )
            
        return diagram 