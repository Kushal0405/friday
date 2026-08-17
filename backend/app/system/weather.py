from __future__ import annotations

import httpx

from app.core.logging import get_logger

logger = get_logger("system.weather")

WMO_CONDITIONS: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


async def get_location() -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://ip-api.com/json/")
            data = resp.json()
            if data.get("status") != "success":
                return None
            return {
                "city": data["city"],
                "region": data["regionName"],
                "country": data["countryCode"],
                "lat": data["lat"],
                "lon": data["lon"],
            }
    except (httpx.HTTPError, KeyError) as exc:
        logger.warning("LOCATION LOOKUP FAILED: %s", exc)
        return None


async def get_weather(lat: float, lon: float) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
                    "timezone": "auto",
                },
            )
            data = resp.json()
            current = data["current"]
            code = current["weather_code"]
            return {
                "temperature_c": current["temperature_2m"],
                "humidity": current["relative_humidity_2m"],
                "wind_kmh": current["wind_speed_10m"],
                "condition": WMO_CONDITIONS.get(code, "Unknown"),
                "weather_code": code,
            }
    except (httpx.HTTPError, KeyError) as exc:
        logger.warning("WEATHER LOOKUP FAILED: %s", exc)
        return None


async def get_weather_snapshot() -> dict | None:
    location = await get_location()
    if not location:
        return None
    weather = await get_weather(location["lat"], location["lon"])
    if not weather:
        return None
    return {**location, **weather}
