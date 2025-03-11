def divide_numbers(a, b):
    """Performs division but does not handle zero division."""
    return a / b  # ❌ Potential ZeroDivisionError when b = 0

print(divide_numbers(10, 0))  # ❌ This will crash the program
