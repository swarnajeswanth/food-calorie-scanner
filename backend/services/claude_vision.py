 
# services/claude_vision.py

import asyncio

import anthropic
import base64
import json
import os
from typing import List
from models.schemas import FoodItem, NutritionInfo

# ─────────────────────────────────────────────
# CLIENT
# Created once, reused for all requests
# Same pattern as creating an axios instance
# ─────────────────────────────────────────────

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)


# ─────────────────────────────────────────────
# PROMPT
# This is the most important part of the service
# We'll refine this heavily in M1.5
# ─────────────────────────────────────────────

FOOD_DETECTION_PROMPT = """
You are an expert nutritionist and food recognition AI.
Analyze this food image and identify all food items present.

For each food item you detect, provide:
1. The food name (be specific - not just "rice" but "basmati rice")
2. Estimated weight in grams based on visual portion size
3. Your confidence level (0.0 to 1.0) in the identification

Return your response as a JSON object with this EXACT structure:
{
    "foods": [
        {
            "name": "food name here",
            "estimated_weight_grams": 000,
            "confidence": 0.00
        }
    ],
    "image_quality": "good/poor/unrecognizable",
    "notes": "any relevant notes about the image or detection"
}

Important rules:
- Detect ALL food items visible, including sides and drinks
- If you cannot identify a food, still include it with low confidence
- If image is not food, return foods as empty array
- Weight estimates should be realistic portions
- Return ONLY the JSON object, no other text
"""


# ─────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────

async def detect_foods_from_image(image_base64: str) -> List[dict]:
    """
    Send image to Claude and get food detections back.
    Returns list of detected foods with weights and confidence.
    """

    # ── Step 1: Detect image format ──────────────
    image_media_type = detect_image_type(image_base64)

    # ── Step 2: Call Claude Vision API ───────────
    message = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": FOOD_DETECTION_PROMPT
                    }
                ]
            }
        ]
    )

    response_text = message.content[0].text
    detected_foods = parse_claude_response(response_text)
    return detected_foods


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def detect_image_type(image_base64: str) -> str:
    """
    Detect image format from base64 string.
    Claude needs to know if it's JPEG, PNG, etc.
    """
    try:
        # Decode first few bytes to check file signature
        header = base64.b64decode(image_base64[:16])

        if header[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif header[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif header[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        elif header[:4] == b'RIFF':
            return "image/webp"
        else:
            # Default to JPEG — most common phone camera format
            return "image/jpeg"

    except Exception:
        return "image/jpeg"


def parse_claude_response(response_text: str) -> List[dict]:
    """
    Parse Claude's JSON response safely.
    Handles cases where Claude adds extra text around the JSON.
    """
    try:
        # ── Attempt 1: Direct JSON parse ─────────
        # Works when Claude returns clean JSON
        return json.loads(response_text)["foods"]

    except json.JSONDecodeError:
        try:
            # ── Attempt 2: Extract JSON from text ─
            # Sometimes Claude adds explanation before/after JSON
            # Find the { and } boundaries
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start != -1 and end != 0:
                json_str = response_text[start:end]
                return json.loads(json_str)["foods"]

        except (json.JSONDecodeError, KeyError):
            pass

    # ── Fallback: Return empty list ───────────────
    # Better to return nothing than crash
    print(f"Failed to parse Claude response: {response_text}")
    return []