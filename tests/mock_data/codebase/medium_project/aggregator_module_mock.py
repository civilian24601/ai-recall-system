"""
aggregator_module_mock.py
Simulates aggregator logic for code searches or data merges.
May produce meltdown triggers if memory usage is 'too high'.
"""

from logging_helpers_mock import log_info, log_error

def aggregator_search(data_list, keyword):
    """
    Searches for a keyword in the data_list.
    If data_list is large, we might meltdown. (Simulated).
    """
    if len(data_list) > 100:
        log_error("Catastrophic meltdown: data_list too large!")
        return []
    return [item for item in data_list if keyword in item]

def aggregator_merge(*lists):
    """
    Merges multiple lists into one. Pretend meltdown if total length > 200
    """
    merged = []
    for lst in lists:
        merged.extend(lst)
    if len(merged) > 200:
        log_error("Catastrophic meltdown: memory overflow in aggregator_merge!")
        return []
    log_info(f"Merged total {len(merged)} items.")
    return merged
