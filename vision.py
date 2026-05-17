"""Screen vision via Groq Llama 4 Scout — free, no extra API key needed."""

import base64
import io
import logging
from PIL import ImageGrab
from groq import Groq, GroqError
from config import GROQ_API_KEY

log = logging.getLogger("hades.vision")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def analyze_screen(prompt: str = "What do you see on this screen? Help me with whatever is on it.") -> str:
    if not client:
        return "Vision system offline — no Groq API key configured, Sir."

    try:
        screenshot = ImageGrab.grab()

        # Resize to save tokens — 1280px wide is plenty for screen reading
        max_width = 1280
        if screenshot.width > max_width:
            ratio = max_width / screenshot.width
            new_size = (max_width, int(screenshot.height * ratio))
            screenshot = screenshot.resize(new_size)

        # Convert to base64 JPEG (smaller than PNG)
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="JPEG", quality=85)
        img_bytes.seek(0)
        image_b64 = base64.standard_b64encode(img_bytes.getvalue()).decode("utf-8")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.5,
        )

        return response.choices[0].message.content.strip()

    except GroqError as e:
        log.error("Groq vision error: %s", e)
        if "rate_limit" in str(e).lower():
            return "I've hit my vision rate limit, Sir. Try again in a moment."
        return f"Vision system error, Sir: {str(e)[:120]}"
    except Exception as e:
        log.exception("Vision error: %s", e)
        return f"Vision system error, Sir: {str(e)[:120]}"
