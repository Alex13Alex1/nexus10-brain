Here is a complete Python script that demonstrates how to interact with a weather API to fetch and display weather data. This is a simplified version focusing on the API integration part using Python and requests library.

```python
# main.py

import requests

# Constants
API_KEY = 'your_openweathermap_api_key'  # Replace with your actual OpenWeatherMap API key
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather?'

def get_weather(city_name):
    """
    Function to get weather data for a given city using OpenWeatherMap API.
    """
    # Construct final url
    complete_url = f"{BASE_URL}q={city_name}&appid={API_KEY}&units=metric"

    # Get response from the server
    response = requests.get(complete_url)

    # Check the HTTP status code
    if response.status_code == 200:
        # Parse JSON data
        data = response.json()

        # Extracting desired data points
        main = data['main']
        wind = data['wind']
        weather = data['weather'][0]

        # Displaying the weather information
        print(f"City: {city_name}")
        print(f"Temperature: {main['temp']}°C")
        print(f"Humidity: {main['humidity']}%")
        print(f"Weather: {weather['description'].capitalize()}")
        print(f"Wind Speed: {wind['speed']} m/s")
    else:
        # If the city is not found or any other error occurs
        print("City not found or API request failed.")

if __name__ == '__main__':
    # Example usage
    city_name = input("Enter city name: ")
    get_weather(city_name)
```

### Key Highlights:
- **API Key and Base URL**: You need to replace `'your_openweathermap_api_key'` with your actual API key from OpenWeatherMap.
- **Units**: The API request includes `&units=metric` to get temperature in Celsius.
- **Error Handling**: Basic error handling is done by checking the HTTP status code.
- **Console Input**: The script takes city input from the user and fetches the weather data for the entered city.

This Python script is ready to be executed in a local environment where Python is installed. The focus is on fetching weather data from OpenWeatherMap; integration with other components like a user interface would require additional implementation using the specified technologies in the technical specification.