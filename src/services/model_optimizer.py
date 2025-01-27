import torch
from torch import nn
from torch.utils.data import DataLoader
from torch.optim import Adam
from torch.quantization import quantize_dynamic

class ModelOptimizer:
    """Optimizes model for faster inference"""
    def __init__(self, model: nn.Module):
        self.model = model
        
    def quantize_model(self):
        """Quantize model for faster inference"""
        self.model = quantize_dynamic(
            self.model,
            {nn.Linear},
            dtype=torch.qint8
        )
        
    def prune_model(self, amount: float = 0.2):
        """Prune model weights"""
        for module in self.model.modules():
            if isinstance(module, nn.Linear):
                prune.l1_unstructured(module, name="weight", amount=amount) 