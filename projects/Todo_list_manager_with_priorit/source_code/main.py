import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Task:
    """Class representing a task with a priority level."""
    id: int
    description: str
    priority: int

class TodoListManager:
    """Manager for handling tasks with priority levels."""
    
    def __init__(self):
        self.tasks: Dict[int, Task] = {}
        self.next_id: int = 1

    def add_task(self, description: str, priority: int) -> Task:
        """Add a new task to the manager."""
        if not description:
            raise ValueError("Task description cannot be empty.")
        task = Task(id=self.next_id, description=description, priority=priority)
        self.tasks[self.next_id] = task
        self.next_id += 1
        return task

    def update_task(self, task_id: int, description: Optional[str] = None, priority: Optional[int] = None) -> Task:
        """Update an existing task."""
        if task_id not in self.tasks:
            raise KeyError(f"Task with id {task_id} does not exist.")
        task = self.tasks[task_id]
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        return task

    def delete_task(self, task_id: int) -> None:
        """Delete a task from the manager."""
        if task_id not in self.tasks:
            raise KeyError(f"Task with id {task_id} does not exist.")
        del self.tasks[task_id]

    def list_tasks(self, sort_by_priority: bool = False) -> List[Task]:
        """List all tasks, optionally sorted by priority."""
        tasks = list(self.tasks.values())
        if sort_by_priority:
            tasks.sort(key=lambda task: task.priority)
        return tasks

def main():
    manager = TodoListManager()
    try:
        # Add tasks
        manager.add_task("Buy groceries", 2)
        manager.add_task("Read a book", 1)
        
        # Update a task
        manager.update_task(1, priority=3)
        
        # List tasks
        tasks = manager.list_tasks(sort_by_priority=True)
        print("Tasks sorted by priority:")
        for task in tasks:
            print(f"Task ID: {task.id}, Description: {task.description}, Priority: {task.priority}")
        
        # Delete a task
        manager.delete_task(1)
        
        # List tasks again
        tasks = manager.list_tasks()
        print("\nTasks after deletion:")
        for task in tasks:
            print(f"Task ID: {task.id}, Description: {task.description}, Priority: {task.priority}")
    
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()