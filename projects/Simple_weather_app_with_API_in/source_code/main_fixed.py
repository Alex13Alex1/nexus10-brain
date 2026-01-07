import os

def fetch_weather_data(location: str) -> dict:
    """
    Fetches current weather data for a given location using a weather API.

    Args:
        location (str): The location for which to fetch the weather data.

    Returns:
        dict: A dictionary containing the weather data.
    """
    # Simulate fetching weather data
    return {"location": location, "temperature": 20, "condition": "Sunny"}

def fetch_forecast_data(location: str) -> dict:
    """
    Fetches weather forecast data for a given location using a weather API.

    Args:
        location (str): The location for which to fetch the forecast data.

    Returns:
        dict: A dictionary containing the forecast data.
    """
    # Simulate fetching forecast data
    return {"location": location, "forecast": [{"day": "Monday", "condition": "Cloudy"}]}

def parse_weather_data(raw_data: dict) -> dict:
    """
    Parses and formats raw weather data.

    Args:
        raw_data (dict): The raw weather data to parse.

    Returns:
        dict: A dictionary containing parsed weather data.
    """
    # Simulate parsing weather data
    return {"parsed_data": raw_data}

def validate_data(data: dict) -> bool:
    """
    Validates the weather data for completeness and correctness.

    Args:
        data (dict): The weather data to validate.

    Returns:
        bool: True if data is valid, False otherwise.
    """
    # Simulate data validation
    return "temperature" in data

def display_current_weather(data: dict) -> None:
    """
    Displays the current weather data.

    Args:
        data (dict): The weather data to display.
    """
    print(f"Current weather in {data['location']}: {data['temperature']}°C, {data['condition']}")

def display_forecast(data: dict) -> None:
    """
    Displays the weather forecast data.

    Args:
        data (dict): The forecast data to display.
    """
    print(f"Weather forecast for {data['location']}:")
    for day in data['forecast']:
        print(f"{day['day']}: {day['condition']}")

def log_error(error_message: str) -> None:
    """
    Logs an error message.

    Args:
        error_message (str): The error message to log.
    """
    print(f"Error: {error_message}")

def handle_error(error_code: int) -> None:
    """
    Handles errors and provides user-friendly messages.

    Args:
        error_code (int): The error code to handle.
    """
    print(f"Handling error with code: {error_code}")

if __name__ == "__main__":
    location = "New York"
    
    print("=" * 40)
    print("🌤️  WEATHER APP DEMO")
    print("=" * 40)
    
    weather_data = fetch_weather_data(location)
    forecast_data = fetch_forecast_data(location)

    if validate_data(weather_data):
        display_current_weather(weather_data)
    else:
        log_error("Invalid weather data")

    print()
    display_forecast(forecast_data)
    
    print("=" * 40)
    print("✅ Demo completed successfully!")
    print("=" * 40)