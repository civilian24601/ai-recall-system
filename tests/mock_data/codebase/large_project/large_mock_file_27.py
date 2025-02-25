# large_mock_file_27.py
"""
LargeProjectFile #27
Compute ratio with meltdown if denominator=0
"""
def meltdown_ratio_27(x, y):
    if y == 0:
        return "Catastrophic meltdown: division by zero"
    return x / y