# CLI Calculator with Operation History
# Nexus v0.8 - AI Factory Ultra

import click
from sympy import sympify
from rich.console import Console

console = Console()
history = []

def evaluate_expression(expression):
    """Safely evaluate mathematical expression using sympy."""
    try:
        result = sympify(expression)
        return result
    except Exception as e:
        console.print(f"[red]Error evaluating expression: {e}[/red]")
        return None

def add_to_history(expression, result):
    """Add operation to history."""
    history.append(f"{expression} = {result}")

def display_result(result):
    """Display calculation result."""
    console.print(f"[green]Result: {result}[/green]")

def display_history():
    """Display operation history."""
    console.print("[cyan]Operation History:[/cyan]")
    for op in history:
        console.print(f"  • {op}")

@click.command()
@click.argument('expression')
def calculate(expression):
    """CLI Calculator - evaluate mathematical expressions safely."""
    result = evaluate_expression(expression)
    if result is not None:
        add_to_history(expression, result)
        display_result(result)
        display_history()

if __name__ == '__main__':
    calculate()
