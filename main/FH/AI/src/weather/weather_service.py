"""Weather service: fetches and normalizes current weather from Open-Meteo.
This module knows HOW to call the weather API — callers (the decision engine)
should never build requests themselves, only consume the normalized result."""

import requests

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 5

# WMO weather codes -> simple condition label (subset covering common cases)
WEATHER_CODE_MAP = {
    0: "clear", 1: "mainly_clear", 2: "partly_cloudy", 3: "overcast",
    45: "fog", 48: "fog",
    51: "drizzle", 53: "drizzle", 55: "drizzle",
    61: "rain", 63: "rain", 65: "heavy_rain",
    71: "snow", 73: "snow", 75: "heavy_snow",
    80: "rain_showers", 81: "rain_showers", 82: "violent_rain_showers",
    95: "thunderstorm", 96: "thunderstorm", 99: "thunderstorm",
}


def fetch_current_weather(latitude, longitude):
    """
    Fetch current weather for one location. Returns a normalized dict,
    or None if the request fails or times out (never raises).
    """
    if latitude is None or longitude is None:
        return None

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,precipitation,relative_humidity_2m,"
                    "wind_speed_10m,wind_direction_10m,surface_pressure,weather_code",
        "timezone": "auto",
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})

        weather_code = current.get("weather_code")
        return {
            "temperature": current.get("temperature_2m"),
            "precipitation": current.get("precipitation"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "pressure": current.get("surface_pressure"),
            "weather_condition": WEATHER_CODE_MAP.get(weather_code, "unknown"),
            "timestamp": current.get("time"),
        }
    except (requests.RequestException, ValueError, KeyError):
        return None

import json
import math


def _cache_key(latitude, longitude):
    """Round coordinates to ~1km precision so nearby sites share a cache entry."""
    lat_rounded = round(latitude, 2)
    lon_rounded = round(longitude, 2)
    return f"weather_{lat_rounded}_{lon_rounded}"


def get_weather_cached(latitude, longitude, redis_instance, ttl_seconds=3600):
    """
    Fetch current weather with Redis caching (default: 1 hour TTL).
    `redis_instance` is passed in explicitly (e.g. from get_redis_instance()
    in main/__init__.py) rather than imported directly, so this module
    doesn't depend on Flask being initialized to be testable standalone.
    """
    if latitude is None or longitude is None:
        return None

    key = _cache_key(latitude, longitude)

    if redis_instance is not None:
        try:
            cached = redis_instance.get(key)
            if cached:
                return json.loads(cached.decode("utf-8"))
        except Exception:
            pass  # cache read failure should never block a live fetch

    result = fetch_current_weather(latitude, longitude)

    if result is not None and redis_instance is not None:
        try:
            redis_instance.setex(key, ttl_seconds, json.dumps(result))
        except Exception:
            pass  # cache write failure should never block returning the result

    return result