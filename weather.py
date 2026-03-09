import requests
from config import WEATHER_API_KEY

def get_weather(city="your city"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        res = requests.get(url).json()
        if res.get("cod") != 200:
            return f"Could not find weather for {city}, Sir."
        desc    = res["weather"][0]["description"].capitalize()
        temp    = res["main"]["temp"]
        feels   = res["main"]["feels_like"]
        humidity= res["main"]["humidity"]
        return (f"Weather in {city.title()}: {desc}. "
                f"Temperature is {temp}°C, feels like {feels}°C, "
                f"humidity at {humidity}%, Sir.")
    except Exception as e:
        return f"Weather service unavailable, Sir. Error: {e}"