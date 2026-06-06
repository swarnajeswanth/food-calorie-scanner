# services/vision_service.py

from openai import OpenAI
import json
import os
import asyncio
from typing import List

# ─────────────────────────────────────────────
# CLIENT SETUP
# OpenRouter uses OpenAI-compatible API
# We just point the base_url to OpenRouter
# ─────────────────────────────────────────────

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# ─────────────────────────────────────────────
# MODEL SELECTION
# Change this if one model isn't working well
# ─────────────────────────────────────────────

MODEL = "sourceful/riverflow-v2.5-pro:free"

# ─────────────────────────────────────────────
# PROMPT
# ─────────────────────────────────────────────

FOOD_DETECTION_PROMPT = """
You are an expert nutritionist and food recognition AI.
Analyze this food image carefully and identify ALL food
items visible.

For each food item detected, provide:
1. Specific food name — be very specific.
   For Indian food: not just "rice" but "basmati rice"
   or "biryani". Identify regional dishes accurately.
2. Estimated weight in grams based on visual portion size
3. Confidence level (0.0 to 1.0) in your identification

Return ONLY a JSON object with this EXACT structure:
{
    "foods": [
        {
            "name": "specific food name",
            "estimated_weight_grams": 000,
            "confidence": 0.00
        }
    ],
    "image_quality": "good/poor/unrecognizable",
    "notes": "any relevant observations"
}

Rules:
- Detect ALL items including sides, drinks, condiments
- List each food separately even if on one plate
- Realistic portion weight estimates
- Empty foods array if no food in image
- Return ONLY the JSON, no other text whatsoever
"""

# ─────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────

async def detect_foods_from_image(image_base64: str) -> List[dict]:
    """
    Send image to OpenRouter vision model.
    Returns list of detected foods with weights and confidence.
    """

    # Detect image format
    media_type = detect_image_type(image_base64)

    # Build image URL for API
    image_url = f"data:{media_type};base64,{image_base64}"

    # Run in thread pool (sync SDK, async server)
    response_text = await asyncio.to_thread(
        call_vision_api,
        image_url
    )

    # Parse response
    detected_foods = parse_response(response_text)

    return detected_foods


# ─────────────────────────────────────────────
# HELPER — Call OpenRouter API (sync)
# ─────────────────────────────────────────────

def call_vision_api(image_url: str) -> str:
    """
    Synchronous API call to OpenRouter.
    Uses OpenAI message format with image_url content type.
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": FOOD_DETECTION_PROMPT
                    }
                ]
            }
        ],
        max_tokens=1024,
        temperature=0.1
    )

    return response.choices[0].message.content


# ─────────────────────────────────────────────
# HELPER — Detect image type
# ─────────────────────────────────────────────

def detect_image_type(image_base64: str) -> str:
    """Detect MIME type from base64 image header."""
    import base64
    try:
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
            return "image/jpeg"
    except Exception:
        return "image/jpeg"


# ─────────────────────────────────────────────
# HELPER — Parse response defensively
# ─────────────────────────────────────────────

def parse_response(response_text: str) -> List[dict]:
    """
    Parse vision model JSON response safely.
    Handles markdown blocks, extra text, etc.
    """

    # Attempt 1 — Direct parse
    try:
        data = json.loads(response_text)
        return data.get("foods", [])
    except json.JSONDecodeError:
        pass

    # Attempt 2 — Strip markdown code blocks
    try:
        cleaned = response_text.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1]
            cleaned = cleaned.split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1]
            cleaned = cleaned.split("```")[0].strip()
        data = json.loads(cleaned)
        return data.get("foods", [])
    except (json.JSONDecodeError, IndexError):
        pass

    # Attempt 3 — Find JSON boundaries
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        if start != -1 and end > start:
            json_str = response_text[start:end]
            data = json.loads(json_str)
            return data.get("foods", [])
    except (json.JSONDecodeError, KeyError):
        pass

    # Fallback
    print(f"⚠️ Could not parse response: {response_text}")
    return []