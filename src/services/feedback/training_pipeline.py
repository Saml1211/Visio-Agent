from datetime import datetime
from pydantic import BaseModel
import torch

class FeedbackSample(BaseModel):
    original_diagram: dict
    user_modified: dict
    feedback_metrics: dict
    timestamp: datetime = datetime.now()

class FeedbackTrainer:
    def __init__(self, model):
        self.model = model
        self.feedback_queue = []
        
    def collect_feedback(self, sample: FeedbackSample):
        """Store feedback for batch training"""
        self.feedback_queue.append(sample)
        
        if len(self.feedback_queue) >= 100:
            self.retrain_model()
            
    def retrain_model(self):
        """Fine-tune model with user feedback"""
        dataset = self._prepare_dataset()
        trainer = torch.utils.data.DataLoader(dataset, batch_size=16)
        
        # Fine-tuning logic
        self.model.train()
        for epoch in range(3):
            for batch in trainer:
                self.model.update(batch)
                
        torch.save(self.model.state_dict(), "retrained_model.pth") 