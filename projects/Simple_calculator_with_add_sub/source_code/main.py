class Calculator:
    """
    A simple calculator class to perform basic arithmetic operations.
    """

    def add(self, a: float, b: float) -> float:
        """
        Returns the sum of a and b.
        """
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """
        Returns the difference of a and b.
        """
        return a - b

    def multiply(self, a: float, b: float) -> float:
        """
        Returns the product of a and b.
        """
        return a * b

    def divide(self, a: float, b: float) -> float:
        """
        Returns the quotient of a and b. Raises an exception if b is zero.
        """
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b


class ErrorHandler:
    """
    A class to handle errors in the calculator operations.
    """

    @staticmethod
    def handle_division_by_zero() -> str:
        """
        Handles division by zero error.
        """
        return "Error: Division by zero is not allowed."

    @staticmethod
    def handle_invalid_input() -> str:
        """
        Handles invalid input error.
        """
        return "Error: Invalid input. Please enter numeric values."


def main():
    """
    Main function to demonstrate the calculator operations.
    """
    calculator = Calculator()
    error_handler = ErrorHandler()

    try:
        # Example operations
        print("Addition: 5 + 3 =", calculator.add(5, 3))
        print("Subtraction: 5 - 3 =", calculator.subtract(5, 3))
        print("Multiplication: 5 * 3 =", calculator.multiply(5, 3))
        print("Division: 5 / 3 =", calculator.divide(5, 3))
        print("Division by zero: 5 / 0 =", calculator.divide(5, 0))
    except ValueError as e:
        print(error_handler.handle_division_by_zero())
    except Exception as e:
        print(error_handler.handle_invalid_input())


if __name__ == "__main__":
    main()