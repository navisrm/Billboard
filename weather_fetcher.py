import os

import httpx
from dotenv import load_dotenv

load_dotenv()

LATITUDE = os.getenv("WEATHER_LAT", "43.2181")
LONGITUDE = os.getenv("WEATHER_LON", "-79.7663")
LOCATION_NAME = os.getenv("WEATHER_LOCATION", "Stoney Creek, ON")

WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Drizzle", "🌦️"),
    55: ("Dense drizzle", "🌦️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Freezing drizzle", "🌧️"),
    61: ("Light rain", "🌧️"),
    63: ("Rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Freezing rain", "🌧️"),
    71: ("Light snow", "🌨️"),
    73: ("Snow", "🌨️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Rain showers", "🌦️"),
    81: ("Rain showers", "🌦️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Snow showers", "🌨️"),
    86: ("Snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm w/ hail", "⛈️"),
    99: ("Thunderstorm w/ hail", "⛈️"),
}

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather():
    response = httpx.get(
        WEATHER_URL,
        params={
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,apparent_temperature,weather_code",
            "temperature_unit": "celsius",
        },
        timeout=10,
    )
    response.raise_for_status()
    current = response.json()["current"]
    description, icon = WEATHER_CODES.get(current["weather_code"], ("Unknown", "🌡️"))
    return {
        "location": LOCATION_NAME,
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "description": description,
        "icon": icon,
    }
