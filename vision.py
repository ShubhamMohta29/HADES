import pyautogui
import google.generativeai as genai
from config import GEMINI_API_KEY
from PIL import Image
import io

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def analyze_screen(prompt="What do you see on this screen? Help me with whatever is on it."):
    # Take screenshot
    screenshot = pyautogui.screenshot()
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    screenshot.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    image = Image.open(img_bytes)

    # Send to Gemini
    response = model.generate_content([prompt, image])
    return response.text