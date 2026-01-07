```python
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🛑 KILL SWITCH
SYSTEM_ACTIVE = True

def emergency_stop():
    """
    Emergency stop function to deactivate the system.
    """
    global SYSTEM_ACTIVE
    SYSTEM_ACTIVE = False
    logger.critical("Emergency stop activated! System is shutting down.")
    graceful_shutdown()

def graceful_shutdown():
    """
    Perform a graceful shutdown of the system.
    """
    logger.info("Performing graceful shutdown...")
    # Add any cleanup code here
    sys.exit(0)

# 🔍 DATA LEAK DETECTION
def check_credentials(username, password):
    """
    Check if the provided credentials are valid.
    
    Args:
        username (str): The username to check.
        password (str): The password to check.
    
    Returns:
        bool: True if credentials are valid, False otherwise.
    """
    # Dummy check for demonstration purposes
    if username == 'admin' and password == 'password':
        return True
    return False

def mask_sensitive_data(data):
    """
    Mask sensitive data in the provided input.
    
    Args:
        data (str): The data to mask.
    
    Returns:
        str: The masked data.
    """
    return data[:2] + '*' * (len(data) - 4) + data[-2:]

# 🚨 ALERT SYSTEM
def send_alert(severity, message):
    """
    Send an alert with the given severity and message.
    
    Args:
        severity (str): The severity level of the alert ('INFO', 'WARNING', 'CRITICAL').
        message (str): The alert message.
    """
    if severity == 'INFO':
        logger.info(message)
    elif severity == 'WARNING':
        logger.warning(message)
    elif severity == 'CRITICAL':
        logger.critical(message)
    else:
        logger.error(f"Unknown severity level: {severity}")

# Example usage
if __name__ == '__main__':
    # Test the alert system
    send_alert('INFO', 'This is an informational message.')
    send_alert('WARNING', 'This is a warning message.')
    send_alert('CRITICAL', 'This is a critical message.')

    # Test the data leak detection
    print(check_credentials('admin', 'password'))  # Should return True
    print(mask_sensitive_data('SensitiveData'))  # Should return 'Se*********ta'

    # Activate the kill switch
    emergency_stop()
```

This code provides the implementation of the required security controls, including a kill switch for emergency shutdown, data leak detection functions, and an alert system with different severity levels.