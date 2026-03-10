import pyautogui
from google import genai
from google.genai import types
from config import GEMINI_API_KEY
import io

client = genai.Client(api_key=GEMINI_API_KEY)

def analyze_screen(prompt="What do you see on this screen? Help me with whatever is on it."):
    try:
        screenshot = pyautogui.screenshot()
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="PNG")
        image_data = img_bytes.getvalue()

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part.from_bytes(data=image_data, mime_type="image/png"),
                prompt
            ]
        )
        return response.text

    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return "I've hit my vision quota limit for today, Sir. I'll be able to see your screen again tomorrow, or you can provide a new API key."
        return f"Vision system error, Sir: {str(e)[:100]}"