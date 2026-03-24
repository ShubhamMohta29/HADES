import base64
import io
from PIL import ImageGrab
import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

def analyze_screen(prompt="What do you see on this screen? Help me with whatever is on it."):
    try:
        # Capture the screen
        screenshot = ImageGrab.grab()
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        screenshot.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        
        # Encode to base64
        image_data = base64.standard_b64encode(img_bytes.getvalue()).decode("utf-8")
        
        # Send to Gemini with image
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content([
            {
                "type": "image",
                "data": image_data,
                "mime_type": "image/png"
            },
            {
                "type": "text",
                "text": prompt
            }
        ])
        
        return response.text

    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return "I've hit my vision quota limit for today, Sir. I'll be able to see your screen again tomorrow, or you can provide a new API key."
        return f"Vision system error, Sir: {str(e)[:100]}"