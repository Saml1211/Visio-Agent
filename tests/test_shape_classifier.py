import pytest
from pathlib import Path
from src.services.shape_classifier import ShapeClassifierService
from src.services.shape_data_prep import ShapeDataPreparer
from src.services.diagram_generation import DiagramGenerationService

@pytest.fixture
def shape_classifier():
    return ShapeClassifierService()

def test_shape_classification(shape_classifier, sample_shape_images):
    """Test shape classification accuracy"""
    results = []
    for image, expected_label in sample_shape_images:
        classification = shape_classifier.classify_shape(image)
        results.append(classification["class_name"] == expected_label)
        
    accuracy = sum(results) / len(results)
    assert accuracy >= 0.95, f"Shape classification accuracy too low: {accuracy}"

def test_model_saving_loading(shape_classifier, tmp_path):
    """Test model saving and loading"""
    model_path = tmp_path / "model.pth"
    shape_classifier.save_model(model_path)
    
    loaded_classifier = ShapeClassifierService(model_path)
    assert loaded_classifier.model is not None
    assert len(loaded_classifier.label_map) > 0 

def test_shape_data_preparation(tmp_path):
    """Test shape data preparation"""
    preparer = ShapeDataPreparer(tmp_path)
    shape_definitions = [
        {
            "type": "display",
            "variants": [{"path": "test_data/display1.png"}]
        }
    ]
    preparer.prepare_dataset(shape_definitions)
    
    assert (tmp_path / "metadata.json").exists()
    
def test_diagram_generation_with_classification():
    """Test diagram generation with shape classification"""
    classifier = ShapeClassifierService("models/shape_classifier.pth")
    generator = DiagramGenerationService(classifier)
    
    components = [
        {
            "image": "test_data/display1.png",
            "position": {"x": 100, "y": 100},
            "metadata": {}
        }
    ]
    
    diagram = generator.generate_diagram(components)
    assert len(diagram.shapes) == 1
    assert diagram.shapes[0].type == "display" 