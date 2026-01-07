# Simple Calculator CLI
# Self-healed by AI Factory v10.5

def add(a: float, b: float) -> float:
    """Returns the sum of a and b."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Returns the difference between a and b."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Returns the product of a and b."""
    return a * b

def divide(a: float, b: float) -> float:
    """Returns the quotient of a and b, handling division by zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

def get_input() -> str:
    """Prompts the user for input and returns it."""
    return input("Enter operation and two numbers (e.g., '+ 3 4'): ")

def validate_input(user_input: str) -> bool:
    """Checks the validity of the input data."""
    parts = user_input.split()
    if len(parts) != 3:
        return False
    operation, num1, num2 = parts
    if operation not in ('+', '-', '*', '/'):
        return False
    try:
        float(num1)
        float(num2)
    except ValueError:
        return False
    return True

def display_result(result: float) -> None:
    """Displays the calculation result on the screen."""
    print(f"Result: {result}")

def handle_error(error: Exception) -> None:
    """Handles errors and displays understandable messages to the user."""
    print(f"Error: {error}")

if __name__ == "__main__":
    print("=" * 40)
    print("  Simple Calculator CLI v1.0")
    print("=" * 40)
    print("Operations: + (add), - (subtract), * (multiply), / (divide)")
    print("Example: + 10 5")
    print()
    
    try:
        user_input = get_input()
        if not validate_input(user_input):
            raise ValueError("Invalid input format. Use: OPERATION NUM1 NUM2")
        
        operation, num1, num2 = user_input.split()
        num1, num2 = float(num1), float(num2)
        
        if operation == '+':
            result = add(num1, num2)
        elif operation == '-':
            result = subtract(num1, num2)
        elif operation == '*':
            result = multiply(num1, num2)
        elif operation == '/':
            result = divide(num1, num2)
        
        display_result(result)
        
    except Exception as e:
        handle_error(e)
