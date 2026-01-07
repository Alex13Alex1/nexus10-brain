# Simple Calculator CLI

## Modules

### 1. Arithmetic Operations Module
- **Description**: This module contains functions for performing basic arithmetic operations: addition, subtraction, multiplication, and division.
- **Functions**:
  - `add(a: float, b: float) -> float`: Returns the sum of `a` and `b`.
  - `subtract(a: float, b: float) -> float`: Returns the difference between `a` and `b`.
  - `multiply(a: float, b: float) -> float`: Returns the product of `a` and `b`.
  - `divide(a: float, b: float) -> float`: Returns the quotient of `a` and `b`, handling division by zero.

### 2. Input Handling Module
- **Description**: This module is responsible for obtaining and validating user input.
- **Functions**:
  - `get_input() -> str`: Prompts the user for input and returns it.
  - `validate_input(user_input: str) -> bool`: Checks the validity of the input data (e.g., checks for non-numeric values).

### 3. Result Display Module
- **Description**: This module is responsible for displaying the results of calculations.
- **Functions**:
  - `display_result(result: float) -> None`: Displays the calculation result on the screen.

### 4. Error Handling Module
- **Description**: This module centrally handles errors and exceptions.
- **Functions**:
  - `handle_error(error: Exception) -> None`: Handles errors and displays understandable messages to the user.

## Data Flow

1. **Input Acquisition**: The user enters data through the command line, which is processed by the input handling module.
2. **Validation**: The entered data is checked for correctness.
3. **Operation Execution**: Depending on the entered operation, the corresponding function from the arithmetic operations module is called.
4. **Error Handling**: If an error occurs (e.g., division by zero), it is handled by the error handling module.
5. **Result Output**: The calculation result is displayed on the screen using the result display module.

## Interfaces

- **User Interface**: Command line through which the user enters data and receives results.
- **Module Interface**: Each module will have clearly defined functions that can be called from other modules.

## Conclusion

The architecture of the Simple Calculator CLI is designed with modularity and ease of use in mind. The separation into modules allows for easy maintenance and expansion of the application's functionality. Data flows ensure consistent processing of user input, operation execution, and result output. Module interfaces ensure clear interaction between different parts of the application. By following this architectural plan, a reliable and efficient CLI application for performing basic arithmetic operations can be created.

```python
# Arithmetic Operations Module
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

# Input Handling Module
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

# Result Display Module
def display_result(result: float) -> None:
    """Displays the calculation result on the screen."""
    print(f"Result: {result}")

# Error Handling Module
def handle_error(error: Exception) -> None:
    """Handles errors and displays understandable messages to the user."""
    print(f"Error: {error}")

if __name__ == "__main__":
    try:
        user_input = get_input()
        if not validate_input(user_input):
            raise ValueError("Invalid input format.")
        
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
```

This code implements a simple command-line calculator that performs basic arithmetic operations. It includes modules for arithmetic operations, input handling, result display, and error handling, following the specified architecture.