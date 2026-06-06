#imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

#import our rotuer
from routes.analyze import router as analyze_router
from routes.feedback import router as feedback_router
from routes.meals import router as meals_router




#load environment variables
load_dotenv()

#creating the FASTAPI Instance
app = FastAPI(
  title="Food Calorie Scanner API",
  description="An API to scan food items and retrieve their calorie information.",
  version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development, restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(analyze_router, prefix="/api", tags=["Analysis"])
app.include_router(feedback_router, prefix="/api", tags=["Feedback"])
app.include_router(meals_router, prefix="/api", tags=["Meals"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Food Calorie Scanner API!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

