class DataAnalysisService:
    def __init__(self, shape_classifier: ShapeClassifierService):
        self.shape_classifier = shape_classifier
        
    def analyze_diagram(self, diagram_path: Path) -> Dict:
        """Analyze a Visio diagram with shape classification"""
        diagram = self._load_diagram(diagram_path)
        analysis_results = {
            "shapes": [],
            "connections": [],
            "metadata": {}
        }
        
        for shape in diagram.shapes:
            classification = self.shape_classifier.classify_shape(shape.image)
            analysis_results["shapes"].append({
                "id": shape.id,
                "type": classification["class_name"],
                "position": shape.position,
                "metadata": self._get_shape_metadata(shape)
            })
            
        return analysis_results
    
    def _get_shape_metadata(self, shape) -> Dict:
        """Extract metadata from a shape"""
        return {
            "text": shape.text,
            "style": shape.style,
            "connections": shape.connections
        } 