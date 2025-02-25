"""
calc_utils_mock.py
Holds some basic math operations, including potential meltdown triggers (divide by zero).
"""

from logging_helpers_mock import log_warning

def safe_divide(a, b):
    """
    Divides a by b safely, returning None if b=0.
    """
    if b == 0:
        log_warning("Divide by zero encountered!")
        return None
    return a / b

def add_values(x, y):
    """
    Simply adds x and y. Strings or non-numbers will produce a TypeError.
    """
    return x + y

def compute_average(numbers):
    """
    Returns the average of a list of numbers, or 0 if empty.
    """
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
