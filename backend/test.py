# test_api.py
import httpx
import base64
import json
from PIL import Image
import io

# ── Load, compress, and encode image ─────────
IMAGE_PATH = "download.jpg"

def compress_image(path: str, max_size: int = 800, quality: int = 85) -> str:
    """Resize and compress image before sending to API."""
    with Image.open(path) as img:
        # Convert RGBA/palette to RGB if needed
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize if larger than max_size on any dimension
        img.thumbnail((max_size, max_size), Image.LANCZOS)

        # Save compressed to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        print(f"Compressed size: {len(encoded)} characters (~{len(encoded)//1024}KB)")
        return encoded

image_base64 = compress_image(IMAGE_PATH)

# ── Send request to our API ───────────────────
payload = {
    "image": image_base64,
    "user_id": "Jeswanth"
}

print("Sending to API...")

response = httpx.post(
    "http://localhost:8000/api/analyze",
    json=payload,
    timeout=60.0          # ← increased timeout
)

print(f"\nStatus Code: {response.status_code}")
print("\nResponse:")
print(json.dumps(response.json(), indent=2))