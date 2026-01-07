```python
import logging
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'

# Initialize JWT Manager
jwt = JWTManager(app)

# Initialize Rate Limiter
limiter = Limiter(app, key_func=get_remote_address)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    """Handle exceptions globally and log them."""
    if isinstance(e, HTTPException):
        return jsonify(error=str(e)), e.code
    logger.error(f"Unhandled exception: {e}")
    return jsonify(error="Internal Server Error"), 500

@app.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token.
    
    Returns:
        JSON response with JWT token or error message.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    # Dummy authentication logic
    if username == 'admin' and password == 'password':
        access_token = create_access_token(identity=username)
        logger.info(f"User {username} logged in successfully.")
        return jsonify(token=access_token), 200
    else:
        logger.warning(f"Failed login attempt for user {username}.")
        return jsonify(error="Invalid credentials"), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
@limiter.limit("5 per minute")
def protected():
    """
    Access protected resource.
    
    Returns:
        JSON response with protected data or error message.
    """
    logger.info("Accessed protected resource.")
    return jsonify(message="Protected data"), 200

if __name__ == '__main__':
    app.run(debug=True)
```

This code provides a basic implementation of a secure REST API using Flask, JWT for authentication, and a rate limiter to control the frequency of requests. It includes logging for monitoring and error handling to manage exceptions gracefully.