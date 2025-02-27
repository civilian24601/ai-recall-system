import os
import json
import shutil
import pytest
from unittest.mock import patch

from code_base.multi_agent_workflow import SingleAgentWorkflow

@pytest.mark.parametrize(
    "mock_filename,user_input,expect_corrupt",
    [
        # (1) small logs + user says "y" => fully resolved
        ("debug_logs_small.json", "y", False),
        # (2) small logs + user says "n" => remains unresolved
        ("debug_logs_small.json", "n", False),
        # (3) medium logs + user says "y"
        ("debug_logs_medium.json", "y", False),
        # (4) large logs + user says "y"
        ("debug_logs_large.json", "y", False),
        # (5) corrupt logs + user says "y" (the script might handle partial or fail gracefully)
        ("debug_logs_corrupt.json", "y", True),
    ]
)
def test_run_workflow_with_various_logs(mock_filename, user_input, expect_corrupt):
    """
    Parametrized test that:
      - Copies the chosen mock_filename into debug_logs_test.json
      - Mocks user input as either 'y' or 'n'
      - Runs SingleAgentWorkflow(test_mode=True)
      - Checks results. For corrupt logs, we expect partial or error handling.
    """

    # 1) Copy the mock file from /tests/mock_data/debug_logs -> /tests/test_logs/debug_logs_test.json
    mock_data_dir = os.path.join("tests", "mock_data", "debug_logs")
    src_path = os.path.join(mock_data_dir, mock_filename)
    test_logs_dir = os.path.join("tests", "test_logs")
    os.makedirs(test_logs_dir, exist_ok=True)

    debug_logs_test_path = os.path.join(test_logs_dir, "debug_logs_test.json")
    
    # Freshly overwrite the test logs
    shutil.copyfile(src_path, debug_logs_test_path)

    # 2) Create the workflow in test_mode
    workflow = SingleAgentWorkflow(test_mode=True)

    # 3) Mock input so the script thinks the user typed user_input
    with patch("builtins.input", return_value=user_input):
        if expect_corrupt:
            # We'll just let it run. The script should log an error & skip.
            workflow.run_workflow()

            # 4A) If the file is truly corrupt, it's still invalid JSON afterwards.
            #     So let's confirm we get a decode error if we attempt to parse it:
            with pytest.raises(json.JSONDecodeError):
                with open(debug_logs_test_path, "r") as f:
                    updated_logs = json.load(f)

            # We'll skip the normal "resolved/unresolved" checks for corrupt logs
            # because we can't parse them anyway. Then do cleanup below.
        else:
            # Normal run
            workflow.run_workflow()
            
            # 4B) Now parse the final logs if it's not corrupt
            with open(debug_logs_test_path, "r") as f:
                updated_logs = json.load(f)
            
            if user_input == "y":
                # Expect at least one resolved
                resolved_count = sum(1 for log in updated_logs if log.get("resolved") is True)
                assert resolved_count > 0, (
                    f"Expected at least one log to become resolved when user_input={user_input}, found none."
                )
            else:
                # user_input=="n" => remain unresolved
                unresolved_count = sum(1 for log in updated_logs if log.get("resolved") is False)
                assert unresolved_count > 0, (
                    f"Expected logs to remain unresolved when user_input={user_input}, found none."
                )
    
    # 5) (Optional) synergy check in debugging_strategy_log_test.json
    # If user_input='y' and not corrupt, we likely updated the snippet success rates.
    strategy_test_path = os.path.join(test_logs_dir, "debugging_strategy_log_test.json")
    if os.path.exists(strategy_test_path):
        with open(strategy_test_path, "r") as f:
            data = json.load(f)
        # If user_input='y' and not corrupt, we expect some success updates
        if user_input == "y" and not expect_corrupt:
            assert any(s.get("success_rate", 0) > 0 for s in data), \
                "Expected a success update in debugging_strategy_log_test.json but found none."
        # If user_input='n' or corrupt, we won't strictly verify
    else:
        # If the script didn't create it, that might be fine if the logs had no fix_attempted
        pass

    # 6) Cleanup or revert the test logs to avoid side effects on the next test
    os.remove(debug_logs_test_path)
    if os.path.exists(strategy_test_path):
        os.remove(strategy_test_path)
