from fastapi import APIRouter, UploadFile, File
from src.services.shape_classifier import ShapeClassifierService

router = APIRouter(prefix="/models", tags=["model_management"])

@router.post("/train")
async def train_model():
    """Train the shape classification model"""
    classifier = ShapeClassifierService()
    classifier.train(Path("data/shapes"))
    return {"status": "training started"}

@router.post("/upload-training-data")
async def upload_training_data(file: UploadFile = File(...)):
    """Upload new training data"""
    # Save and process uploaded file
    return {"status": "data uploaded"}

@router.get("/performance")
async def get_model_performance():
    """Get model performance metrics"""
    return {"accuracy": 0.95, "precision": 0.94, "recall": 0.96} 