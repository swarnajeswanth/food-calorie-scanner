# services/gemini_vision.py

import google.generativeai as genai
import base64
import json
import os
import asyncio
from typing import List

# ─────────────────────────────────────────────
# CONFIGURE GEMINI CLIENT
# ─────────────────────────────────────────────

# in gemini_vision.py — inside generate_content()
generation_config=genai.types.GenerationConfig(
    temperature=0.1,
    max_output_tokens=2048,   # ← was 1024, double it
)

model = genai.GenerativeModel("gemini-2.0-flash")


# ─────────────────────────────────────────────
# PROMPT
# Same logic as before — engineered for
# structured JSON output
# ─────────────────────────────────────────────

FOOD_DETECTION_PROMPT = """
You are an expert nutritionist and food recognition AI.
Analyze this food image carefully and identify ALL food 
items visible in the image.

For each food item detected, provide:
1. Specific food name (not just "rice" but "basmati rice"
   or "biryani rice". Identify regional foods accurately
   including Indian, Asian, Middle Eastern dishes)
2. Estimated weight in grams based on visual portion size
   and standard serving sizes
3. Confidence level (0.0 to 1.0) in your identification

Return your response as a JSON object with this 
EXACT structure and nothing else:
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

Critical rules:
- Detect ALL items including sides, drinks, condiments
- Be specific with regional cuisine names
- If multiple foods on one plate, list each separately
- Weight should reflect realistic portion sizes
- If image has no food, return empty foods array
- Return ONLY the JSON, absolutely no other text
"""


# ─────────────────────────────────────────────
# MAIN FUNCTION
# ─────────────────────────────────────────────

async def detect_foods_from_image(image_base64: str) -> List[dict]:
    """
    Send image to Gemini and get food detections back.
    Returns list of detected foods with weights and confidence.
    """

    # ── Step 1: Prepare image for Gemini ─────────
    image_data = prepare_image(image_base64)

    # ── Step 2: Call Gemini Vision API ───────────
    # Run in thread pool to avoid blocking async loop
    response = await asyncio.to_thread(
        generate_content,
        image_data
    )

    # ── Step 3: Parse the response ────────────────
    detected_foods = parse_gemini_response(response)

    return detected_foods


# ─────────────────────────────────────────────
# HELPER — Prepare image data
# ─────────────────────────────────────────────

def prepare_image(image_base64: str) -> dict:
    """
    Convert base64 string to Gemini image format.
    Gemini accepts inline image data directly.
    """
    # Detect image type from base64 header
    media_type = detect_image_type(image_base64)

    return {
        "mime_type": media_type,
        "data": image_base64
    }


# ─────────────────────────────────────────────
# HELPER — Call Gemini (sync, run in thread)
# ─────────────────────────────────────────────

def generate_content(image_data: dict) -> str:
    """
    Synchronous Gemini API call.
    Called via asyncio.to_thread to avoid blocking.
    """
    response = model.generate_content(
        contents=[
            {
                "parts": [
                    {
                        "inline_data": image_data
                    },
                    {
                        "text": FOOD_DETECTION_PROMPT
                    }
                ]
            }
        ],
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,    
            # ↑ Low temperature = more consistent,
            #   deterministic responses
            #   0.0 = always same answer
            #   1.0 = creative/varied answers
            #   For food detection we want consistency
            
            max_output_tokens=1024,
        )
    )

    return response.text


# ─────────────────────────────────────────────
# HELPER — Detect image format
# ─────────────────────────────────────────────

def detect_image_type(image_base64: str) -> str:
    """
    Detect image MIME type from base64 header bytes.
    """
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
            return "image/jpeg"  # default

    except Exception:
        return "image/jpeg"


# ─────────────────────────────────────────────
# HELPER — Parse Gemini response safely
# ─────────────────────────────────────────────

def parse_gemini_response(response_text: str) -> List[dict]:
    """
    Parse Gemini's JSON response defensively.
    Handles extra text, markdown code blocks, etc.
    """

    # ── Attempt 1: Direct JSON parse ─────────────
    try:
        data = json.loads(response_text)
        return data.get("foods", [])
    except json.JSONDecodeError:
        pass

    # ── Attempt 2: Strip markdown code blocks ─────
    # Gemini sometimes wraps JSON in ```json ... ```
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

    # ── Attempt 3: Find JSON boundaries ──────────
    try:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1

        if start != -1 and end > start:
            json_str = response_text[start:end]
            data = json.loads(json_str)
            return data.get("foods", [])
    except (json.JSONDecodeError, KeyError):
        pass

    # ── Fallback ──────────────────────────────────
    print(f"⚠️ Could not parse Gemini response:")
    print(response_text)
    return []