```python
import json
import hashlib
import jwt
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any

SECRET_KEY = "your_secret_key"

class SimpleRESTAPI(BaseHTTPRequestHandler):
    users = {}

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json") -> None:
        """Sets the HTTP headers for the response."""
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.end_headers()

    def do_POST(self) -> None:
        """Handles POST requests for login and registration."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        if self.path == "/login":
            self.handle_login(data)
        elif self.path == "/register":
            self.handle_register(data)
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode())

    def handle_login(self, data: Dict[str, Any]) -> None:
        """Handles user login by verifying credentials and returning a JWT token."""
        username = data.get("username")
        password = data.get("password")

        if username in self.users and self.users[username] == hashlib.sha256(password.encode()).hexdigest():
            token = jwt.encode({"username": username}, SECRET_KEY, algorithm="HS256")
            self._set_headers(200)
            self.wfile.write(json.dumps({"token": token}).encode())
        else:
            self._set_headers(401)
            self.wfile.write(json.dumps({"error": "Invalid credentials"}).encode())

    def handle_register(self, data: Dict[str, Any]) -> None:
        """Handles user registration by storing hashed passwords."""
        username = data.get("username")
        password = data.get("password")

        if username in self.users:
            self._set_headers(409)
            self.wfile.write(json.dumps({"error": "User already exists"}).encode())
        else:
            self.users[username] = hashlib.sha256(password.encode()).hexdigest()
            self._set_headers(201)
            self.wfile.write(json.dumps({"message": "User registered successfully"}).encode())

def run(server_class=HTTPServer, handler_class=SimpleRESTAPI, port=8080) -> None:
    """Runs the HTTP server."""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd server on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
```

### Fixes Made:
1. **Syntax Error**: The comment at the beginning of the file was improperly formatted, causing a syntax error. Ensure all comments are properly formatted with `#` at the start of each line.
2. **File Path Error**: The file path for execution was incorrect. Ensure the correct path is used when executing the file to avoid file not found errors.