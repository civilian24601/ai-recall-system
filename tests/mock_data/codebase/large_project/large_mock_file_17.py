# large_mock_file_17.py
"""
LargeProjectFile #17
Aggregator style partial search.
"""
def partial_search_17(data, fragment):
    results = []
    for d in data:
        if fragment.lower() in d.lower():
            results.append(d)
    return results