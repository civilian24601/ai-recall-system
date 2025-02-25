# large_mock_file_13.py
"""
LargeProjectFile #13
Simulates chunking references.
"""
def chunk_data_13(data, chunk_size=10):
    return [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
