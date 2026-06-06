

from fastapi import APIRouter, HTTPException
from models.schemas import FeedbackRequest, FeedbackResponse
import uuid

router = APIRouter()


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    summary="Submit correction for a food scan",
    description="Store user corrections to improve future AI predictions"
)
async def submit_feedback(request: FeedbackRequest):
   

    # Generate unique feedback ID
    feedback_id = str(uuid.uuid4())

   
    print(f"Feedback received for scan: {request.scan_id}")
    print(f"Original: {request.original_food_name}")
    print(f"Corrected: {request.corrected_food_name}")

    return FeedbackResponse(
        success=True,
        message="Feedback received. Thank you for helping us improve!",
        feedback_id=feedback_id
    )