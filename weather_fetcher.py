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


# Groups weather codes into the sky animations the dashboard header knows how to draw.
def _condition(code):
    if code in (0, 1):
        return "clear"
    if code == 2:
        return "partly"
    if code == 3:
        return "cloudy"
    if code in (45, 48):
        return "fog"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (95, 96, 99):
        return "storm"
    if 51 <= code <= 82:
        return "rain"
    return "cloudy"


def get_weather():
    response = httpx.get(
        WEATHER_URL,
        params={
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "current": "temperature_2m,apparent_temperature,weather_code,is_day",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "auto",
            "forecast_days": 1,
            "temperature_unit": "celsius",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    current = data["current"]
    daily = data["daily"]
    description, icon = WEATHER_CODES.get(current["weather_code"], ("Unknown", "🌡️"))
    return {
        "location": LOCATION_NAME,
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "description": description,
        "icon": icon,
        "condition": _condition(current["weather_code"]),
        "is_day": bool(current["is_day"]),
        "high": daily["temperature_2m_max"][0],
        "low": daily["temperature_2m_min"][0],
    }
