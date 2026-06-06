from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest, AnalyzeResponse,NutritionInfo, FoodItem
from services.vision_service import detect_foods_from_image
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

  # #mock response for now
  # mock_nutrition = {
  #   "calories": 250.0,
  #   "protein": 10.0,
  #   "carbohydrates": 30.0,
   
  #   "fats": 8.0,
  #   "fiber": 5.0,
  #   "sugar": 12.0
  # }

  # mock_food_item = {
  #   "name": "Spaghetti Bolognese",
  #   "estimated_weight_grams": 350.0,
  #   "confidence": 0.85,
  #   "nutrition": mock_nutrition,
  #   "usda_food_id": "12345"
  # }

  # mock_response = {
  #   "scan_id": scan_id,
  #   "foods": [mock_food_item],
  #   "total_nutrition": mock_nutrition,
  #   "overall_confidence": 0.85,
  #   "timestamp": datetime.utcnow()
  # }
 # ── Step 3: Call Claude Vision ────────────────
  try:
      detected_foods = await detect_foods_from_image(request.image)
  except Exception as e:
      raise HTTPException(
          status_code=500,
          detail=f"AI analysis failed: {str(e)}"
      )

  # ── Step 4: Handle no foods detected ──────────
  if not detected_foods:
      raise HTTPException(
          status_code=422,
          detail="No food items detected in image. Please try a clearer photo."
      )

  # ── Step 5: Build FoodItem list ───────────────
  # For now use placeholder nutrition
  # USDA integration comes in M1.6
  food_items = []
  total_calories = 0
  total_protein = 0
  total_carbohydrates = 0
  total_fats = 0
  total_fiber = 0
  total_sugar = 0
  confidence_scores = []

  for food in detected_foods:
      # Placeholder nutrition per 100g
      # Will be replaced with USDA data in M1.6
      placeholder_nutrition = NutritionInfo(
          calories=200.0,
          protein=10.0,
          carbohydrates=25.0,
          fats=8.0,
          fiber=2.0,
          sugar=5.0
      )

      food_item = FoodItem(
          name=food["name"],
          estimated_weight_grams=food["estimated_weight_grams"],
          confidence=food["confidence"],
          nutrition=placeholder_nutrition,
          usda_food_id=None
      )

      food_items.append(food_item)
      confidence_scores.append(food["confidence"])

      # Accumulate totals
      weight_ratio = food["estimated_weight_grams"] / 100
      total_calories += 200.0 * weight_ratio
      total_protein += 10.0 * weight_ratio
      total_carbohydrates += 25.0 * weight_ratio
      total_fats += 8.0 * weight_ratio
      total_fiber += 2.0 * weight_ratio
      total_sugar += 5.0 * weight_ratio

  # ── Step 6: Calculate totals ──────────────────
  total_nutrition = NutritionInfo(
      calories=round(total_calories, 1),
      protein=round(total_protein, 1),
      carbohydrates=round(total_carbohydrates, 1),
      fats=round(total_fats, 1),
      fiber=round(total_fiber, 1),
      sugar=round(total_sugar, 1)
  )

  overall_confidence = round(
      sum(confidence_scores) / len(confidence_scores), 2
  )

  # ── Step 7: Return response ───────────────────
  return AnalyzeResponse(
      scan_id=scan_id,
      foods=food_items,
      total_nutrition=total_nutrition,
      overall_confidence=overall_confidence,
      timestamp=datetime.utcnow()
  )

