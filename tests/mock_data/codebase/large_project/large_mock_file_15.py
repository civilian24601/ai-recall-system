# large_mock_file_15.py
"""
LargeProjectFile #15
Another meltdown triggered if input_size > 500
"""
def meltdown_trigger_15(input_size):
    if input_size > 500:
        return "Catastrophic meltdown: memory overflow"
    return "No meltdown triggered."