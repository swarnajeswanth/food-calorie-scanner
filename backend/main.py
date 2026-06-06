#imports
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

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

@app.get("/")
async def root():
    return {"message": "Welcome to the Food Calorie Scanner API!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

