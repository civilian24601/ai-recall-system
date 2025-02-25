import time
import sys
import json
import datetime
import re
import os
from agent_manager import AgentManager

class SingleAgentWorkflow:
    """Executes AI recall, debugging, and code retrieval workflows in single-agent mode."""

    def __init__(self):
        self.agent_manager = AgentManager()
        self.debug_log_file = "../logs/debug_logs.json"
        self.test_scripts_dir = "./test_scripts/"
        self.ai_timeout = 300

    def generate_log_id(self, prefix="log"):
        """Generates a unique ID for debugging log entries."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}"

    def retrieve_past_debug_logs(self):
        """Retrieve past debugging logs from local storage."""
        print("🔍 Retrieving past debugging logs...")
        try:
            with open(self.debug_log_file, "r") as f:
                logs = json.load(f)
                if not logs:
                    print("⚠ No debugging logs found.")
                    return []
                print(f"✅ Retrieved {len(logs)} logs.")
                return logs
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Debugging log file missing or corrupted. Error: {e}")
            return []

    def run_workflow(self):
        """Executes a structured AI debugging & recall workflow for ALL pending issues."""
        print("\n🚀 Starting Single-Agent AI Workflow...\n")

        past_debug_logs = self.retrieve_past_debug_logs()
        if not past_debug_logs:
            print("❌ No past debugging logs available.")
            return

        print(f"🔍 Checking for unresolved debugging issues...")
        unresolved_logs = [
            log for log in past_debug_logs 
            if log.get("resolved") is False and "stack_trace" in log
        ]

        if not unresolved_logs:
            print("✅ No unresolved debugging issues found.")
            return

        print(f"🔍 Found {len(unresolved_logs)} unresolved logs to process.")

        for error_entry in unresolved_logs:
            script_name = error_entry.get("stack_trace", "").split("'")[1] if "stack_trace" in error_entry else None
            if not script_name:
                print(f"⚠ Skipping log entry with missing `stack_trace`: {error_entry}")
                continue

            print(f"🔹 AI will attempt to fix `{script_name}` based on debugging logs.")

            script_path = os.path.join(self.test_scripts_dir, script_name)
            script_content = ""
            if os.path.exists(script_path):
                with open(script_path, "r") as f:
                    script_content = f.read()

            if not script_content.strip():
                print(f"⚠ `{script_name}` is empty or unavailable. Skipping AI fix.")
                continue

            print("🔹 AI Analyzing Debugging Logs...")
            ai_fix_suggestion = self.agent_manager.delegate_task(
                "debug",
                f"Analyze `{script_name}` and find the source of the following error: {error_entry['error']}. "
                "Read the script below and determine how to correctly fix it."
                "Your response MUST ONLY contain the corrected function inside triple backticks (```python ... ```), NO explanations."
                "\nHere is the current content of `{script_name}`:\n"
                "```python\n"
                f"{script_content}\n"
                "```",
                timeout=self.ai_timeout
            )

            extracted_fix = self.agent_manager.preprocess_ai_response(ai_fix_suggestion)

            print(f"✅ AI Suggested Fix:\n{extracted_fix}\n")
            confirmation = input("Did the fix work? (y/n): ").strip().lower()
            fix_verified = confirmation == "y"

            error_entry["fix_attempted"] = extracted_fix
            error_entry["resolved"] = fix_verified
            error_entry["fix_successful"] = fix_verified

            try:
                with open(self.debug_log_file, "r") as f:
                    logs = json.load(f)

                for i, entry in enumerate(logs):
                    if entry["id"] == error_entry["id"]:
                        logs[i] = error_entry  # Update existing log entry

                with open(self.debug_log_file, "w") as f:
                    json.dump(logs, f, indent=4)

                print("✅ Debugging log successfully updated in `debug_logs.json`.")

            except Exception as e:
                print(f"❌ Failed to update debugging log: {e}")

        print("\n✅ Single-Agent AI Workflow Completed!\n")

# 🚀 Example Usage
if __name__ == "__main__":
    workflow = SingleAgentWorkflow()
    workflow.run_workflow()
