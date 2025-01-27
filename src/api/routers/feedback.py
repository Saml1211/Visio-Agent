from fastapi import APIRouter
from services.feedback import FeedbackTrainer

router = APIRouter()
trainer = FeedbackTrainer()

@router.post("/feedback")
async def submit_feedback(sample: FeedbackSample):
    trainer.collect_feedback(sample)
    return {"status": "feedback received"} 