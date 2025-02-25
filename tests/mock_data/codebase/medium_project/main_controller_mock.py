"""
main_controller_mock.py
The central 'controller' referencing multiple modules 
(db_manager_mock, aggregator_module_mock, etc.).
"""

import db_manager_mock
import aggregator_module_mock
import multi_agent_mock
import stats_processor_mock
from logging_helpers_mock import log_info

def run_system_check():
    """
    Demonstrates how we might tie together aggregator logic, DB usage, stats, etc.
    """
    db_ok = db_manager_mock.connect_to_database()
    if db_ok:
        query_res = db_manager_mock.run_query("SELECT 'hello' FROM dual")
        db_manager_mock.disconnect_database()
        log_info(f"run_system_check retrieved: {query_res}")
    
    big_data = [f"item{i}" for i in range(120)]
    meltdown_test = aggregator_module_mock.aggregator_search(big_data, "item50")
    log_info(f"Aggregator meltdown search result length: {len(meltdown_test)}")

    multi_res = multi_agent_mock.run_multi_agent_flow(
        data_segments=[["alpha", "beta"], ["gamma", "beta", "delta"]], 
        search_keyword="beta"
    )
    log_info(f"multi_agent_flow found: {multi_res}")

    ratio = stats_processor_mock.calculate_ratio(100, 20)
    log_info(f"Calculated ratio = {ratio}")

if __name__ == "__main__":
    run_system_check()
