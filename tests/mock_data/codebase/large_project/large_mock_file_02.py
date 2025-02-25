# large_mock_file_02.py
"""
LargeProjectFile #02
Might reference meltdown scenario if data too large.
"""
def mock_function_02(data):
    if len(data) > 200:
        return "Catastrophic meltdown: memory overflow"
    return f"Data length is {len(data)}"