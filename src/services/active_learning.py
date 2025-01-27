from typing import List, Dict
from pathlib import Path
import torch
from torch.utils.data import Dataset
from src.services.shape_classifier import ShapeClassifierService
from PIL import Image

class ActiveLearningDataset(Dataset):
    """Dataset for active learning"""
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.samples = []
        
    def add_sample(self, image_path: Path, label: str):
        """Add a new sample to the dataset"""
        self.samples.append({
            "image_path": image_path,
            "label": label
        })
        
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        image = Image.open(sample["image_path"])
        return image, sample["label"]

class ActiveLearningService:
    """Service for active learning"""
    def __init__(self, classifier: ShapeClassifierService):
        self.classifier = classifier
        self.dataset = ActiveLearningDataset(Path("data/active_learning"))
        
    def update_model(self, new_samples: List[Dict]):
        """Update model with new samples"""
        for sample in new_samples:
            self.dataset.add_sample(sample["image_path"], sample["label"])
            
        # Fine-tune model
        self.classifier.fine_tune(self.dataset) 