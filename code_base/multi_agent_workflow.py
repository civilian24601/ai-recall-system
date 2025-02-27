import time
import sys
import json
import datetime
import re
import os
import logging
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the parent directory of code_base to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .agent_manager import AgentManager
from .debugging_strategy import DebuggingStrategy  # [NEW] We import it here so we can link them

class SingleAgentWorkflow:
    """Executes AI recall, debugging, and code retrieval workflows in single-agent mode."""

    def __init__(self, test_mode=False):
        """
        If test_mode=True, we switch to test logs and 'debugging_logs_test' for Chroma.
        Otherwise, we use 'debug_logs.json' & 'debugging_logs' for production.
        """
        self.agent_manager = AgentManager()
        
        # [NEW] Switch local JSON path based on test_mode
        if test_mode:
            self.debug_log_file = "tests/test_logs/debug_logs_test.json"
        else:
            self.debug_log_file = "../logs/debug_logs.json"

        self.test_scripts_dir = "./test_scripts/"
        self.ai_timeout = 300

        # Initialize Chroma client for debug logs
        self.chroma_client = chromadb.PersistentClient(
            path="/mnt/f/projects/ai-recall-system/chroma_db/"
        )
        
        # [NEW] Pick test vs. production collection name
        self.debug_collection_name = "debugging_logs_test" if test_mode else "debugging_logs"
        self.debugging_logs_collection = self.chroma_client.get_or_create_collection(
            name=self.debug_collection_name
        )

        # [NEW] Also create a DebuggingStrategy instance, using the same test_mode
        self.debugging_strategy = DebuggingStrategy(test_mode=test_mode)

    def generate_log_id(self, prefix="log"):
        """Generates a unique ID for debugging log entries."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}"

    def retrieve_past_debug_logs(self):
        """Retrieve past debugging logs from local storage."""
        logging.info("Retrieving past debugging logs...")
        try:
            with open(self.debug_log_file, "r") as f:
                logs = json.load(f)
                valid_logs = []
                for log in logs:
                    if "id" in log and "error" in log and "stack_trace" in log:
                        valid_logs.append(log)
                    else:
                        logging.warning(f"Skipping invalid log entry: {log}")
                if not valid_logs:
                    logging.warning("No valid debugging logs found.")
                    return []
                logging.info(f"Retrieved {len(valid_logs)} valid logs.")
                return valid_logs
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Debugging log file missing or corrupted. Error: {e}")
            return []

    def sync_debug_log_with_chroma(self, entry):
        """
        Upserts the updated debug log entry into the 'debugging_logs' (or 'debugging_logs_test') collection.
        Each entry is stored as a separate document with ID = entry["id"].
        """
        try:
            doc_json = json.dumps(entry)
            metadata = {
                "error": entry.get("error", ""),
                "timestamp": entry.get("timestamp", ""),
                "resolved": entry.get("resolved", False),
                "fix_successful": entry.get("fix_successful", False),
            }
            existing_docs = self.debugging_logs_collection.get(ids=[entry["id"]])
            if (existing_docs 
                and "documents" in existing_docs 
                and existing_docs["documents"]):
                self.debugging_logs_collection.update(
                    ids=[entry["id"]],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
                logging.info(f"Updated log entry '{entry['id']}' in Chroma collection '{self.debug_collection_name}'.")
            else:
                self.debugging_logs_collection.add(
                    ids=[entry["id"]],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
                logging.info(f"Added new log entry '{entry['id']}' to Chroma collection '{self.debug_collection_name}'.")
        except Exception as e:
            logging.error(f"Failed to sync debug log with Chroma: {e}")

    def run_workflow(self):
        """Executes a structured AI debugging & recall workflow for ALL pending issues."""
        logging.info("Starting Single-Agent AI Workflow...")

        past_debug_logs = self.retrieve_past_debug_logs()
        if not past_debug_logs:
            logging.error("No past debugging logs available.")
            return

        logging.info("Checking for unresolved debugging issues...")
        unresolved_logs = [
            log for log in past_debug_logs
            if log.get("resolved") is False and "stack_trace" in log
        ]

        if not unresolved_logs:
            logging.info("No unresolved debugging issues found.")
            return

        logging.info(f"Found {len(unresolved_logs)} unresolved logs to process.")

        for error_entry in unresolved_logs:
            script_name = None
            stack_trace = error_entry.get("stack_trace", "")
            # e.g. "File 'test_db_handler.py', line 9, in connect_to_database"
            # We'll parse out the script name by splitting on quotes
            parts = stack_trace.split("'")
            if len(parts) >= 2:
                script_name = parts[1]

            if not script_name:
                logging.warning(f"Skipping log entry with missing `stack_trace`: {error_entry}")
                continue

            logging.info(f"AI will attempt to fix `{script_name}` based on debugging logs.")

            script_path = os.path.join(self.test_scripts_dir, script_name)
            script_content = ""
            if os.path.exists(script_path):
                with open(script_path, "r") as f:
                    script_content = f.read()

            if not script_content.strip():
                logging.warning(f"`{script_name}` is empty or unavailable. Skipping AI fix.")
                continue

            logging.info("AI Analyzing Debugging Logs...")
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

            logging.info(f"AI Suggested Fix:\n{extracted_fix}\n")
            confirmation = input("Did the fix work? (y/n): ").strip().lower()
            fix_verified = (confirmation == "y")

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

                logging.info("Debugging log successfully updated in `debug_logs.json`.")

                # **UPSET to Chroma** (real-time sync)
                self.sync_debug_log_with_chroma(error_entry)

            except Exception as e:
                logging.error(f"Failed to update debugging log: {e}")

            # [NEW] Also update the DebuggingStrategy with success/fail 
            # if we have a recognized 'error' and an AI snippet
            if "error" in error_entry and extracted_fix:
                logging.info("Updating the debugging strategy with fix success/failure...")
                self.debugging_strategy.update_strategy(
                    error_type=error_entry["error"],
                    snippet=extracted_fix,
                    success=fix_verified
                )

        logging.info("Single-Agent AI Workflow Completed!")

# 🚀 Example Usage
if __name__ == "__main__":
    # For production: test_mode=False
    workflow = SingleAgentWorkflow(test_mode=False)
    workflow.run_workflow()
