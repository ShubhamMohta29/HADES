import requests
from config import WEATHER_API_KEY


def get_weather(city: str = "your city") -> str:
    if not WEATHER_API_KEY:
        return "Weather service offline — no API key configured, Sir."
    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": WEATHER_API_KEY, "units": "metric"}
        res = requests.get(url, params=params, timeout=8).json()
        if res.get("cod") != 200:
            return f"Could not find weather for {city}, Sir."
        desc    = res["weather"][0]["description"].capitalize()
        temp    = res["main"]["temp"]
        feels   = res["main"]["feels_like"]
        humidity = res["main"]["humidity"]
        return (f"Weather in {city.title()}: {desc}. "
                f"Temperature is {temp}°C, feels like {feels}°C, "
                f"humidity at {humidity}%, Sir.")
    except requests.Timeout:
        return "The weather service is taking too long to respond, Sir."
    except Exception as e:
        return f"Weather service unavailable, Sir. Error: {e}"
