def process_data(input_data):
    """Processes data but does not handle NoneType values."""
    return input_data["value"] + 10  # ❌ TypeError if 'value' is None

# Simulated test case
data = {"value": None}
process_data(data)  # ❌ Causes TypeError: unsupported operand type(s)
