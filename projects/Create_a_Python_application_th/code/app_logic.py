```python
import requests
import pandas as pd
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='btc_tracker.log')

# Constants
API_URL = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
CSV_FILE = 'bitcoin_price_data.csv'
PRICE_CHANGE_THRESHOLD = 0.01  # 1% change

def fetch_bitcoin_price():
    """Fetch the current price of Bitcoin from the public API."""
    try:
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise an error for bad responses
        price_data = response.json()
        return price_data['bitcoin']['usd']
    except requests.RequestException as e:
        logging.error(f"Error fetching Bitcoin price: {e}")
        return None

def save_price_to_csv(price):
    """Save the current price of Bitcoin to a CSV file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df = pd.DataFrame([[timestamp, price]], columns=['Timestamp', 'Price'])
    df.to_csv(CSV_FILE, mode='a', header=not pd.io.common.file_exists(CSV_FILE), index=False)

def check_price_change(new_price):
    """Check if the price change exceeds the defined threshold and print a warning."""
    try:
        df = pd.read_csv(CSV_FILE)
        last_price = df.iloc[-1]['Price']
        percentage_change = abs((new_price - last_price) / last_price)
        if percentage_change > PRICE_CHANGE_THRESHOLD:
            logging.warning(f"Price change alert: {percentage_change:.2%}")
            print(f"Warning: Bitcoin price changed by {percentage_change:.2%}")
    except (FileNotFoundError, IndexError) as e:
        logging.warning(f"Could not check price change: {e}")

def main():
    """Main function to run the Bitcoin price tracker."""
    while True:
        price = fetch_bitcoin_price()
        if price is not None:
            save_price_to_csv(price)
            check_price_change(price)
        time.sleep(60)  # Wait for 1 minute before next check

if __name__ == "__main__":
    main()
```

This script will track the Bitcoin price every minute, save the data to a CSV file, and print a warning if the price changes by more than 1%. It uses the CoinGecko API to fetch prices and handles errors and logging appropriately.