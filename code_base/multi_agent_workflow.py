import time
import sys
import json
import datetime
import re
import os
import chromadb  
# Add the parent directory of code_base to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_manager import AgentManager

class SingleAgentWorkflow:
    """Executes AI recall, debugging, and code retrieval workflows in single-agent mode."""

    def __init__(self, test_mode=False):
        """
        If test_mode=True, we might switch to 'debugging_logs_test' for Chroma.
        Otherwise, we use 'debugging_logs' for production.
        """
        self.agent_manager = AgentManager()
        self.debug_log_file = "../logs/debug_logs.json"
        self.test_scripts_dir = "./test_scripts/"
        self.ai_timeout = 300

        # Initialize Chroma client for debug logs
        self.chroma_client = chromadb.PersistentClient(
            path="/mnt/f/projects/ai-recall-system/chroma_db/"
        )
        self.debug_collection_name = "debugging_logs_test" if test_mode else "debugging_logs"
        self.debugging_logs_collection = self.chroma_client.get_or_create_collection(
            name=self.debug_collection_name
        )

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

    def sync_debug_log_with_chroma(self, entry):
        """
        Upserts the updated debug log entry into the 'debugging_logs' (or 'debugging_logs_test') collection.
        Each entry is stored as a separate document with ID = entry["id"].
        """
        doc_json = json.dumps(entry)
        metadata = {
            "error": entry.get("error", ""),
            "timestamp": entry.get("timestamp", ""),
            "resolved": entry.get("resolved", False),
            "fix_successful": entry.get("fix_successful", False),
        }
        self.debugging_logs_collection.add(
            ids=[entry["id"]],
            documents=[doc_json],
            metadatas=[metadata]
        )
        print(f"🔄 Synced log entry '{entry['id']}' to Chroma collection '{self.debug_collection_name}'.")

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
            script_name = None
            stack_trace = error_entry.get("stack_trace", "")
            # e.g. "File 'test_db_handler.py', line 9, in connect_to_database"
            # We'll parse out the script name by splitting on quotes
            parts = stack_trace.split("'")
            if len(parts) >= 2:
                script_name = parts[1]

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
                (
                    f"Analyze `{script_name}` and find the source of the following error: {error_entry['error']}. "
                    "Your response MUST ONLY contain the corrected function inside triple backticks (```python ...```), NO explanations.\n"
                    f"Here is the current content of `{script_name}`:\n"
                    "```python\n"
                    f"{script_content}\n"
                    "```"
                ),
                timeout=self.ai_timeout
            )

            extracted_fix = self.agent_manager.preprocess_ai_response(ai_fix_suggestion)

            print(f"✅ AI Suggested Fix:\n{extracted_fix}\n")
            confirmation = input("Did the fix work? (y/n): ").strip().lower()
            fix_verified = confirmation == "y"

            # Update the local JSON record
            error_entry["fix_attempted"] = extracted_fix
            error_entry["resolved"] = fix_verified
            error_entry["fix_successful"] = fix_verified

            # For logging, optionally set a timestamp if missing
            if "timestamp" not in error_entry:
                error_entry["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                # Update local JSON
                with open(self.debug_log_file, "r") as f:
                    logs = json.load(f)

                for i, entry in enumerate(logs):
                    if entry["id"] == error_entry["id"]:
                        logs[i] = error_entry  # Update existing log entry

                with open(self.debug_log_file, "w") as f:
                    json.dump(logs, f, indent=4)

                print("✅ Debugging log successfully updated in `debug_logs.json`.")

                # **UPSET to Chroma** (real-time sync)
                self.sync_debug_log_with_chroma(error_entry)

            except Exception as e:
                print(f"❌ Failed to update debugging log: {e}")

        print("\n✅ Single-Agent AI Workflow Completed!\n")


# 🚀 Example Usage
if __name__ == "__main__":
    workflow = SingleAgentWorkflow(test_mode=False)  # or True if you want test collection
    workflow.run_workflow()
# ✅ Example Output
# 
# 🚀 Starting Single-Agent AI Workflow...
# 
# 🔍 Retrieving past debugging logs...
# ✅ Retrieved 3 logs.
# 🔍 Checking for unresolved debugging issues...
# 🔍 Found 2 unresolved logs to process.
# 🔹 AI will attempt to fix `test_db_handler.py` based on debugging logs.
# 🔹 AI Analyzing Debugging Logs...
# ✅ AI Suggested Fix:
# def connect_to_database(db_name, user, password):
#     # Your fix here...
#     pass
# 
# Did the fix work? (y/n): y
# ✅ Debugging log successfully updated in `debug_logs.json`.
# 🔄 Synced log entry 'log_20210927_154200' to Chroma collection 'debugging_logs'.
# 🔹 AI will attempt to fix `test_db_handler.py` based on debugging logs.
# 🔹 AI Analyzing Debugging Logs...
# ✅ AI Suggested Fix:
# def connect_to_database(db_name, user, password):
#     # Your fix here...
#     pass
# 
# Did the fix work? (y/n): n
# ✅ Debugging log successfully updated in `debug_logs.json`.
# 🔄 Synced log entry 'log_20210927_154201' to Chroma collection 'debugging_logs'.
# 
# ✅ Single-Agent AI Workflow Completed!
# 
# In this example, the script reads past debugging logs from a local JSON file and processes unresolved issues. For each issue, it retrieves the script content, sends a task to the AI agent, and prompts the user to verify the fix. The script then updates the local JSON file and syncs the updated log entry to the Chroma collection.
# 
# This workflow demonstrates the integration of AI agents, local file storage, and a cloud-based database to manage debugging logs and AI-driven fixes.
# 
# You can customize the workflow by adding more error handling, logging, or AI tasks to enhance the debugging and recall capabilities of the system.
# 
# This script can be extended to handle more complex workflows, multiple agents, or additional data sources to create a comprehensive AI-driven debugging and recall system.
# 
# For more advanced features, consider integrating with other tools, APIs, or services to enhance the AI capabilities and improve the efficiency of the debugging and recall processes.
# 
# By combining AI agents, local storage, and cloud databases, you can build a robust system for managing debugging logs, analyzing issues, and generating AI-driven fixes to streamline the software development and debugging process.