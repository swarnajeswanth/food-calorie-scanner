from pydantic import BaseModel,Field
from typing import List,Optional
from datetime import datetime

class NutritionInfo(BaseModel):
  calories:float = Field(...,description="Total calories (kcal)",ge=0)
  protein:float = Field(...,description="Protein in grams",ge=0)
  carbohydrates:float = Field(...,description="Carbohydrates in grams",ge=0)
  fats:float = Field(...,description="Fats in grams",ge=0)
  fiber:Optional[float] = Field(None,description="Fiber in grams",ge=0)
  sugar:Optional[float] = Field(None,description="Sugar in grams",ge=0)



class FoodItem(BaseModel):
  name:str = Field(...,description="Dected food name",min_length=1)
  estimated_weight_grams:float= Field(...,description="Estimated weight of the food item in grams",ge=0)
  nutrition:NutritionInfo = Field(...,description="Calculated nutrition for this portion")
  usda_food_id:Optional[str] = Field(None,description="USDA Food Database ID if available")


#Analyze Request and Response Models
class AnalyzeRequest(BaseModel):
  image_url:str = Field(...,description="Base64 encoded image ")
  user_id:Optional[str] = Field(default="anonymous",description="Optional user identifier for personalized recommendations")


class AnalyzeResponse(BaseModel):
  scan_id:str = Field(...,description="Unique identifier for this scan")
  foods:List[FoodItem] = Field(...,description="List of detected food items with their nutritional information")
  total_nutrition:NutritionInfo = Field(...,description="Average confidence score for the detected food items")
  timestamp:datetime = Field(...,description="Timestamp of when the analysis was performed")


class FeedbackRequest(BaseModel):
    scan_id: str = Field(..., description="The scan being corrected")
    original_food_name: str = Field(..., description="What AI detected")
    corrected_food_name: Optional[str] = Field(default=None, description="What it actually was")
    original_calories: float = Field(..., description="Calories AI estimated")
    corrected_calories: Optional[float] = Field(default=None, description="Actual calories", ge=0)
    original_weight_grams: float = Field(..., description="Weight AI estimated")
    corrected_weight_grams: Optional[float] = Field(default=None, description="Actual weight", gt=0)
    user_id: Optional[str] = Field(default="anonymous")


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str

    
class MealRecord(BaseModel):
  scan_id:str
  user_id:str
  foods:List[FoodItem]
  total_nutrition:NutritionInfo
  timestamp:datetime

class MealHistory(BaseModel):
  user_id:Optional[str]
  meals:List[MealRecord]
  total_count:int
