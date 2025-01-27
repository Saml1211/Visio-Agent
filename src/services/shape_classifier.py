import torch
import torch.nn as nn
from torchvision import models
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import classification_report
from typing import List, Dict, Tuple
import json
from pathlib import Path

class VisioShapeDataset(Dataset):
    """Dataset for Visio shape classification"""
    def __init__(self, data_dir: Path, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        with open(data_dir / "metadata.json") as f:
            self.metadata = json.load(f)
        
    def __len__(self):
        return len(self.metadata)
    
    def __getitem__(self, idx):
        item = self.metadata[idx]
        image = Image.open(self.data_dir / item["image_path"])
        label = item["label"]
        
        if self.transform:
            image = self.transform(image)
            
        return image, label

class ShapeClassifier(nn.Module):
    """CNN-based shape classifier"""
    def __init__(self, num_classes: int):
        super().__init__()
        self.model = models.resnet50(pretrained=True)
        self.model.fc = nn.Sequential(
            nn.Linear(self.model.fc.in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, num_classes)
        )
        
    def forward(self, x):
        return self.model(x)

class ShapeClassifierService:
    """Service for shape identification and classification"""
    def __init__(self, model_path: Path = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_path) if model_path else None
        self.label_map = {}
        self.reverse_label_map = {}
        
    def train(self, data_dir: Path, num_epochs: int = 10):
        """Train the shape classifier"""
        dataset = VisioShapeDataset(data_dir)
        self.label_map = dataset.label_map
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}
        
        train_loader = DataLoader(dataset, batch_size=32, shuffle=True)
        self.model = ShapeClassifier(len(self.label_map)).to(self.device)
        
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)
        
        for epoch in range(num_epochs):
            self.model.train()
            for images, labels in train_loader:
                images, labels = images.to(self.device), labels.to(self.device)
                
                optimizer.zero_grad()
                outputs = self.model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                
            print(f"Epoch {epoch+1}/{num_epochs}, Loss: {loss.item()}")
            
    def classify_shape(self, image) -> Dict:
        """Classify a Visio shape"""
        if not self.model:
            raise ValueError("Model not loaded or trained")
            
        self.model.eval()
        with torch.no_grad():
            image = self.transform(image).unsqueeze(0).to(self.device)
            output = self.model(image)
            _, predicted = torch.max(output, 1)
            class_id = predicted.item()
            
        return {
            "class_id": class_id,
            "class_name": self.reverse_label_map[class_id],
            "confidence": torch.softmax(output, dim=1)[0][class_id].item()
        }
        
    def save_model(self, model_path: Path):
        """Save the trained model"""
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "label_map": self.label_map
        }, model_path)
        
    def _load_model(self, model_path: Path):
        """Load a pre-trained model"""
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model = ShapeClassifier(len(checkpoint["label_map"]))
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.label_map = checkpoint["label_map"]
        self.reverse_label_map = {v: k for k, v in self.label_map.items()}
        return self.model 