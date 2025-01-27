# Shape Identification and Classification

## Overview
The shape identification and classification system uses deep learning to recognize and categorize Visio shapes. It consists of:

1. **Data Preparation**: Tools for preparing training data
2. **Model Training**: Pipeline for training the classification model
3. **Shape Classification**: Service for classifying shapes in diagrams
4. **Integration**: Seamless integration with data analysis and diagram generation

## Usage

### Preparing Training Data
```python
from src.services.shape_data_prep import ShapeDataPreparer

preparer = ShapeDataPreparer(Path("data/shapes"))
preparer.prepare_dataset(shape_definitions)
```

### Training the Model
```python
from src.services.shape_classifier import ShapeClassifierService

classifier = ShapeClassifierService()
classifier.train(Path("data/shapes"))
classifier.save_model(Path("models/shape_classifier.pth"))
```

### Using the Classifier
```python
classifier = ShapeClassifierService(Path("models/shape_classifier.pth"))
classification = classifier.classify_shape(image)
print(classification)
```

## Architecture
The system uses a ResNet50-based CNN with custom classification head. Key features:
- Transfer learning from ImageNet
- Customizable number of classes
- GPU acceleration support
- Model saving and loading 

## Advanced Features

### Active Learning
The system supports active learning to continuously improve the model:
```python
from src.services.active_learning import ActiveLearningService

active_learner = ActiveLearningService(classifier)
active_learner.update_model(new_samples)
```

### Relationship Detection
Detect relationships between shapes:
```python
from src.services.relationship_detector import RelationshipDetector

detector = RelationshipDetector()
relationships = detector.detect_relationships(diagram)
```

### Model Optimization
Optimize model for faster inference:
```python
from src.services.model_optimizer import ModelOptimizer

optimizer = ModelOptimizer(model)
optimizer.quantize_model()
optimizer.prune_model()
```

### Metadata Extraction
Extract text and metadata from shapes:
```python
from src.services.shape_metadata_extractor import ShapeMetadataExtractor

extractor = ShapeMetadataExtractor()
metadata = extractor.extract_metadata(shape)
``` 