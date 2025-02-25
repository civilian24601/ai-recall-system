def calculate_ratio(numerator, denominator):
    """Calculates ratio but does not handle ZeroDivisionError."""
    return numerator / denominator  # ❌ Crashes when denominator = 0

# Simulated test case
result = calculate_ratio(10, 0)  # ❌ Causes ZeroDivisionError
