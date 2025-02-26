#!/usr/bin/env python3
"""
test_debugging_strategy.py

A test script that references debugging_strategy.py from code_base.
It uses test logs in /tests/test_logs/ and mock JSON from /tests/mock_data/debug_logs/.
"""

import os
import sys
import json

# 1) Adjust the import path so we can import DebuggingStrategy from code_base
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(PARENT_DIR)

from code_base.debugging_strategy import DebuggingStrategy

class TestDebuggingStrategy:
    """
    A test harness that overrides debugging_strategy.py's file paths to:
      - debug_logs_file -> /tests/test_logs/debug_logs_test.json
      - strategy_log_file -> /tests/test_logs/debugging_strategy_log_test.json

    Then we load mock data (small/medium/large) from:
      /tests/mock_data/debug_logs/*.json
    and run 'analyze_previous_fixes()' to see if snippet deduping & success rates work.
    """

    def __init__(self):
        # We'll keep these logs separate from your main logs folder
        self.test_logs_dir = os.path.join(SCRIPT_DIR, "test_logs")
        # Ensure /tests/test_logs/ exists (in case it's not created yet)
        if not os.path.exists(self.test_logs_dir):
            os.makedirs(self.test_logs_dir)

        # Create an instance of DebuggingStrategy
        self.strategy = DebuggingStrategy()
        # Overwrite the paths to point to /tests/test_logs/
        self.strategy.debug_logs_file = os.path.join(self.test_logs_dir, "debug_logs_test.json")
        self.strategy.strategy_log_file = os.path.join(self.test_logs_dir, "debugging_strategy_log_test.json")

    def load_mock_json(self, mock_json_filename):
        """
        Copies the given mock JSON (like debug_logs_small.json) from
        /tests/mock_data/debug_logs/ into /tests/test_logs/debug_logs_test.json
        so the strategy's analyze_previous_fixes() can read it.
        """
        # Path to your mock_data debug logs
        mock_data_dir = os.path.join(SCRIPT_DIR, "mock_data", "debug_logs")
        src_path = os.path.join(mock_data_dir, mock_json_filename)
        dst_path = self.strategy.debug_logs_file  # debug_logs_test.json

        if not os.path.exists(src_path):
            print(f"⚠ Could not find mock JSON: {src_path}")
            return False

        with open(src_path, "r") as src_file:
            data = json.load(src_file)

        with open(dst_path, "w") as out_file:
            json.dump(data, out_file, indent=2)

        print(f"Loaded mock data from {src_path} -> {dst_path}")
        return True

    def run_test(self, mock_json_filename, description):
        """
        General method to load a mock JSON log, run 'analyze_previous_fixes()',
        and print a short summary. 'description' clarifies which scenario is tested.
        """
        print(f"\n=== Running Test: {description} ===")
        if not self.load_mock_json(mock_json_filename):
            print("Skipping test due to missing mock file.")
            return

        self.strategy.analyze_previous_fixes()
        print(f"Test '{description}' completed. Check {self.strategy.strategy_log_file} for updated strategies.")

    def cleanup_test_logs(self):
        """
        Optional method to remove or reset the test logs after each run, if desired.
        """
        for fname in ["debug_logs_test.json", "debugging_strategy_log_test.json"]:
            path = os.path.join(self.test_logs_dir, fname)
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    tester = TestDebuggingStrategy()

    # Example usage: test small, medium, and large mock logs
    # Adjust filenames if you want more scenarios.

    tester.run_test("debug_logs_small.json", "Small logs test")
    tester.run_test("debug_logs_medium.json", "Medium logs test")
    tester.run_test("debug_logs_large.json", "Large logs test")

    # If you want to remove test logs after, you can:
    # tester.cleanup_test_logs()
