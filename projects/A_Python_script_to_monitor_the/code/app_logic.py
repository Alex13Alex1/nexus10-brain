```python
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# Constants
BTC_PRICE_THRESHOLD = 80000
CHECK_INTERVAL = 300  # Check every 5 minutes
EMAIL_ADDRESS = "your_email@example.com"
EMAIL_PASSWORD = "your_email_password"
SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
RECIPIENT_EMAIL = "recipient_email@example.com"

def get_btc_price():
    """
    Fetch the current price of BTC using the CoinGecko API.
    Returns the current price in USD.
    """
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd")
        response.raise_for_status()
        data = response.json()
        return data['bitcoin']['usd']
    except (requests.RequestException, ValueError) as e:
        print(f"Error fetching BTC price: {e}")
        return None

def send_email_alert(price):
    """
    Sends an email alert if the BTC price falls below the threshold.
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = "BTC Price Alert"
        
        body = f"The current price of BTC is ${price}, which is below your threshold of ${BTC_PRICE_THRESHOLD}."
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, text)
        server.quit()
        print("Email alert sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def monitor_btc_price():
    """
    Monitors the BTC price and sends an alert if the price drops below the threshold.
    """
    while True:
        price = get_btc_price()
        if price is not None:
            print(f"Current BTC price: ${price}")
            if price < BTC_PRICE_THRESHOLD:
                send_email_alert(price)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_btc_price()
```

This script periodically checks the BTC price using the CoinGecko API. If the price drops below $80,000, it sends an email alert to the specified recipient. You'll need to replace the email credentials and server details with your own to use the script.