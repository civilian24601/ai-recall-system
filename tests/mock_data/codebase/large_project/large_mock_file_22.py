# large_mock_file_22.py
"""
LargeProjectFile #22
Minimal aggregator approach #2
"""
def aggregator_min_22(data, key):
    return [d for d in data if d.startswith(key)]