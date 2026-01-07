from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs


class TaskManager:
    """Simple in-memory task manager."""
    
    def __init__(self):
        self.tasks: Dict[int, Dict[str, Any]] = {}
        self.next_id: int = 1
    
    def create_task(self, title: str, description: str = "", priority: int = 1) -> Dict[str, Any]:
        """Create a new task."""
        task = {
            "id": self.next_id,
            "title": title,
            "description": description,
            "priority": priority,
            "completed": False
        }
        self.tasks[self.next_id] = task
        self.next_id += 1
        return task
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> list:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def update_task(self, task_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        """Update a task."""
        if task_id not in self.tasks:
            return None
        self.tasks[task_id].update(kwargs)
        return self.tasks[task_id]
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def complete_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Mark a task as completed."""
        return self.update_task(task_id, completed=True)


# Global task manager instance
task_manager = TaskManager()


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the REST API."""
    
    def _send_json_response(self, data: Any, status: int = 200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _parse_body(self) -> dict:
        """Parse JSON body from request."""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            body = self.rfile.read(content_length)
            return json.loads(body.decode())
        return {}
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        
        if parsed.path == '/tasks':
            tasks = task_manager.get_all_tasks()
            self._send_json_response({"tasks": tasks, "count": len(tasks)})
        
        elif parsed.path.startswith('/tasks/'):
            try:
                task_id = int(parsed.path.split('/')[-1])
                task = task_manager.get_task(task_id)
                if task:
                    self._send_json_response(task)
                else:
                    self._send_json_response({"error": "Task not found"}, 404)
            except ValueError:
                self._send_json_response({"error": "Invalid task ID"}, 400)
        
        elif parsed.path == '/health':
            self._send_json_response({"status": "healthy", "version": "1.0.0"})
        
        else:
            self._send_json_response({"error": "Not found"}, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/tasks':
            data = self._parse_body()
            if 'title' not in data:
                self._send_json_response({"error": "Title is required"}, 400)
                return
            
            task = task_manager.create_task(
                title=data['title'],
                description=data.get('description', ''),
                priority=data.get('priority', 1)
            )
            self._send_json_response(task, 201)
        else:
            self._send_json_response({"error": "Not found"}, 404)
    
    def do_PUT(self):
        """Handle PUT requests."""
        if self.path.startswith('/tasks/'):
            try:
                task_id = int(self.path.split('/')[-1])
                data = self._parse_body()
                task = task_manager.update_task(task_id, **data)
                if task:
                    self._send_json_response(task)
                else:
                    self._send_json_response({"error": "Task not found"}, 404)
            except ValueError:
                self._send_json_response({"error": "Invalid task ID"}, 400)
        else:
            self._send_json_response({"error": "Not found"}, 404)
    
    def do_DELETE(self):
        """Handle DELETE requests."""
        if self.path.startswith('/tasks/'):
            try:
                task_id = int(self.path.split('/')[-1])
                if task_manager.delete_task(task_id):
                    self._send_json_response({"message": "Task deleted"})
                else:
                    self._send_json_response({"error": "Task not found"}, 404)
            except ValueError:
                self._send_json_response({"error": "Invalid task ID"}, 400)
        else:
            self._send_json_response({"error": "Not found"}, 404)
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[API] {args[0]}")


def run_server(host: str = 'localhost', port: int = 8000):
    """Run the REST API server."""
    server = HTTPServer((host, port), APIHandler)
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           🚀 REST API Task Manager v1.0                      ║
╠══════════════════════════════════════════════════════════════╣
║  Server running at: http://{host}:{port}                      ║
║                                                              ║
║  Endpoints:                                                  ║
║    GET    /tasks          - List all tasks                   ║
║    GET    /tasks/<id>     - Get a task                       ║
║    POST   /tasks          - Create a task                    ║
║    PUT    /tasks/<id>     - Update a task                    ║
║    DELETE /tasks/<id>     - Delete a task                    ║
║    GET    /health         - Health check                     ║
║                                                              ║
║  Press Ctrl+C to stop                                        ║
╚══════════════════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] Server stopped.")
        server.shutdown()


if __name__ == "__main__":
    # Demo mode - create some tasks and show them
    print("=" * 50)
    print("🧪 DEMO MODE - Testing Task Manager")
    print("=" * 50)
    
    # Create tasks
    task1 = task_manager.create_task("Buy groceries", "Milk, eggs, bread", priority=2)
    task2 = task_manager.create_task("Finish report", "Q4 financial report", priority=1)
    task3 = task_manager.create_task("Call mom", priority=3)
    
    print(f"\n✅ Created {len(task_manager.get_all_tasks())} tasks:")
    for task in task_manager.get_all_tasks():
        status = "✓" if task["completed"] else "○"
        print(f"  [{status}] #{task['id']}: {task['title']} (priority: {task['priority']})")
    
    # Update a task
    task_manager.complete_task(1)
    print(f"\n📝 Completed task #1")
    
    # Show updated list
    print(f"\n📋 Current tasks:")
    for task in task_manager.get_all_tasks():
        status = "✓" if task["completed"] else "○"
        print(f"  [{status}] #{task['id']}: {task['title']}")
    
    print("\n" + "=" * 50)
    print("✅ Demo completed! To start the server, uncomment run_server()")
    print("=" * 50)
    
    # Uncomment to start the server:
    # run_server()
