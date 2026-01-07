import random
import string
from typing import Tuple, Dict
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from passlib.context import CryptContext

app = Flask(__name__)
api = Api(app)

# Password context for hashing and verifying
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_password(length: int, complexity: str) -> str:
    """
    Generates a password based on the specified length and complexity.
    
    :param length: Length of the password.
    :param complexity: Complexity level of the password ('low', 'medium', 'high').
    :return: Generated password as a string.
    """
    if complexity == 'low':
        chars = string.ascii_lowercase
    elif complexity == 'medium':
        chars = string.ascii_letters + string.digits
    elif complexity == 'high':
        chars = string.ascii_letters + string.digits + string.punctuation
    else:
        raise ValueError("Invalid complexity level. Choose 'low', 'medium', or 'high'.")
    
    return ''.join(random.choice(chars) for _ in range(length))

class PasswordGenerator(Resource):
    def post(self) -> Tuple[Dict[str, str], int]:
        """
        Handles POST requests to generate a password.
        
        :return: JSON response with the generated password.
        """
        try:
            data = request.get_json()
            length = data.get('length')
            complexity = data.get('complexity')
            
            if not isinstance(length, int) or length <= 0:
                return {"error": "Invalid length. Must be a positive integer."}, 400
            
            password = generate_password(length, complexity)
            return {"password": password}, 200
        
        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            return {"error": "An unexpected error occurred."}, 500

api.add_resource(PasswordGenerator, '/generate-password')

if __name__ == "__main__":
    app.run(debug=True)