"""
stats_processor_mock.py
Combines calc_utils_mock for advanced stats. 
"""

import calc_utils_mock
from logging_helpers_mock import log_warning

def calculate_ratio(numerator, denominator):
    """
    Returns ratio of numerator/denominator or 'None' if denominator=0.
    """
    return calc_utils_mock.safe_divide(numerator, denominator)

def sum_and_average(values):
    """
    Adds all values, then returns (sum, average).
    If any item is non-numeric, logs a warning.
    """
    total = 0
    for v in values:
        if not isinstance(v, (int, float)):
            log_warning(f"Non-numeric value encountered: {v}")
            continue
        total += v
    avg = calc_utils_mock.compute_average(values)
    return total, avg
