# large_mock_file_28.py
"""
LargeProjectFile #28
Chunk test #2 for aggregator
"""
def chunker_28(items, n=5):
    return [items[i:i+n] for i in range(0, len(items), n)]
