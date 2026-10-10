import requests

def get_weather(lat: float, lng: float) -> dict:
    """Get current and 5-hour forecast weather information for given coordinates.

    Args:
        lat (float): Latitude of the location (e.g., 27.7172).
        lng (float): Longitude of the location (e.g., 85.3240).

    Returns:
        dict: Weather summary including current conditions and next 5 hours forecast.
    """
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lng}&current_weather=true"
        f"&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,windspeed_10m,rain"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to retrieve weather data: {str(e)}"}

    current_weather = data.get("current_weather", {})
    hourly_data = data.get("hourly", {})

    if not current_weather or not hourly_data:
        return {"error": "Weather data unavailable for these coordinates."}

    time_entries = hourly_data.get("time", [])
    limit = min(5, len(time_entries))

    forecast = [
        {
            "time": time_entries[i],
            "temperature_2m": hourly_data["temperature_2m"][i],
            "apparent_temperature": hourly_data["apparent_temperature"][i],
            "relative_humidity_2m": hourly_data["relative_humidity_2m"][i],
            "windspeed_10m": hourly_data["windspeed_10m"][i],
            "rain": hourly_data["rain"][i],
        }
        for i in range(limit)
    ]

    return {
        "current_weather": current_weather,
        "next_5_hours": forecast,
    }