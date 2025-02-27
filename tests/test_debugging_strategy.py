import os
import json
import shutil
import pytest

from code_base.debugging_strategy import DebuggingStrategy

@pytest.mark.parametrize("mock_filename, expect_corrupt", [
    ("debug_logs_small.json", False),
    ("debug_logs_medium.json", False),
    ("debug_logs_large.json", False),
    ("debug_logs_corrupt.json", True),
])
def test_analyze_previous_fixes_param(mock_filename, expect_corrupt):
    """
    Parametrized test for DebuggingStrategy.analyze_previous_fixes().
    Copies mock_filename -> debug_logs_test.json, 
    then calls .analyze_previous_fixes() in test_mode.
    """

    mock_data_dir = os.path.join("tests", "mock_data", "debug_logs")
    src_path = os.path.join(mock_data_dir, mock_filename)

    test_logs_dir = os.path.join("tests", "test_logs")
    os.makedirs(test_logs_dir, exist_ok=True)

    debug_logs_test_path = os.path.join(test_logs_dir, "debug_logs_test.json")
    debugging_strategy_test_path = os.path.join(test_logs_dir, "debugging_strategy_log_test.json")

    # Copy the chosen mock file to debug_logs_test.json
    shutil.copyfile(src_path, debug_logs_test_path)

    # If there's an old strategy log, remove it
    if os.path.exists(debugging_strategy_test_path):
        os.remove(debugging_strategy_test_path)

    # Create a DebuggingStrategy in test_mode
    strategy = DebuggingStrategy(test_mode=True)

    # Now call analyze_previous_fixes()
    # If 'corrupt' is True, we might see partial or no logs processed
    # We'll just let it run. If your code gracefully logs an error, that's fine.
    strategy.analyze_previous_fixes()

    # Check if debugging_strategy_log_test.json was created or partially updated
    if os.path.exists(debugging_strategy_test_path):
        with open(debugging_strategy_test_path, "r") as f:
            data = json.load(f)

        if expect_corrupt:
            # Possibly data might be empty or partial, let's not be too strict
            pass
        else:
            # For normal logs, we expect at least something
            assert len(data) > 0, f"Expected some strategy entries for {mock_filename}, found none."
    else:
        # If file doesn't exist, maybe the logs were fully corrupt or no fix_attempted
        if not expect_corrupt:
            pytest.fail(f"Expected {debugging_strategy_test_path} to be created for {mock_filename}, but it wasn't.")

    # Cleanup: remove both logs
    if os.path.exists(debug_logs_test_path):
        os.remove(debug_logs_test_path)
    if os.path.exists(debugging_strategy_test_path):
        os.remove(debugging_strategy_test_path)


def test_update_strategy_directly():
    """
    Non-parametrized test: we directly call .update_strategy() 
    to ensure it creates an entry in debugging_strategy_log_test.json.
    """
    test_logs_dir = os.path.join("tests", "test_logs")
    os.makedirs(test_logs_dir, exist_ok=True)

    debug_logs_test_path = os.path.join(test_logs_dir, "debug_logs_test.json")
    strategy_log_path = os.path.join(test_logs_dir, "debugging_strategy_log_test.json")

    # Clean up any old logs
    if os.path.exists(debug_logs_test_path):
        os.remove(debug_logs_test_path)
    if os.path.exists(strategy_log_path):
        os.remove(strategy_log_path)

    # Create DebuggingStrategy
    strategy = DebuggingStrategy(test_mode=True)

    snippet = """```python
def divide(a, b):
    return a / b
```"""

    # We'll add a new record with success=True
    strategy.update_strategy("ZeroDivisionError: division by zero", snippet, success=True)

    # Now check debugging_strategy_log_test.json
    assert os.path.exists(strategy_log_path), "Expected strategy log to be created."

    with open(strategy_log_path, "r") as f:
        data = json.load(f)

    # Exactly 1 new record 
    matching = [
        s for s in data 
        if s["error_type"] == "ZeroDivisionError: division by zero"
    ]
    assert len(matching) == 1, "Did not find exactly one record for ZeroDivisionError snippet."

    rec = matching[0]
    assert rec.get("success_rate") == 1.0, "Expected success_rate of 1.0 for a single success."

    # Cleanup
    if os.path.exists(strategy_log_path):
        os.remove(strategy_log_path)
