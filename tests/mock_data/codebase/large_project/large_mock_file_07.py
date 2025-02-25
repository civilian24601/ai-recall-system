# large_mock_file_07.py
"""
LargeProjectFile #07
Returns string referencing meltdown scenario or not.
"""
def meltdown_scenario_07(flag):
    if flag:
        return "Catastrophic meltdown: recursion depth exceeded"
    return "All good here."