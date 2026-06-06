from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest, AnalyzeResponse
import uuid 
from datetime import datetime

router = APIRouter()

@router.post("/analyze",   
             response_model=AnalyzeResponse,
             summary="Analyze a food image and return nutritional information",description="Accepts a base64 encoded image of food, processes it to identify the food items, and returns their estimated nutritional information."
)
async def analyze_food(request: AnalyzeRequest):
  #validate image exists
  if not request.image or len(request.image) <100:
    raise HTTPException(status_code=400, detail="Invalid image data. Please provide a valid base64 encoded image.")
  
  #generate a unique scan ID
  scan_id = str(uuid.uuid4())

  #mock response for now
  mock_nutrition = {
    "calories": 250.0,
    "protein": 10.0,
    "carbohydrates": 30.0,
   
    "fats": 8.0,
    "fiber": 5.0,
    "sugar": 12.0
  }

  mock_food_item = {
    "name": "Spaghetti Bolognese",
    "estimated_weight_grams": 350.0,
    "confidence": 0.85,
    "nutrition": mock_nutrition,
    "usda_food_id": "12345"
  }

  mock_response = {
    "scan_id": scan_id,
    "foods": [mock_food_item],
    "total_nutrition": mock_nutrition,
    "overall_confidence": 0.85,
    "timestamp": datetime.utcnow()
  }

  return mock_response
