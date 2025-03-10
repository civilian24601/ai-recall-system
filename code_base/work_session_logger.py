import datetime
import json
import time
import traceback

import chromadb

from .network_utils import detect_api_url

class WorkSessionLogger:
    """Handles AI work session logging, retrieval, and structured summaries."""

    def __init__(self, test_mode=False):  # [CHANGED] add test_mode param
        """
        If test_mode=True, we write to 'tests/test_logs/work_session_test.md'
        and use 'work_sessions_test' collection. Otherwise we do the production path.
        """
        if test_mode:
            self.session_log_file = "tests/test_logs/work_session_test.md"  # [NEW]
            collection_name = "work_sessions_test"                           # [NEW]
        else:
            self.session_log_file = "../logs/work_session.md"
            collection_name = "work_sessions"

        self.chroma_client = chromadb.PersistentClient(
            path="/mnt/f/projects/ai-recall-system/chroma_db/"
        )
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)

        self.api_url = detect_api_url()
        print(f"🔹 Using API URL: {self.api_url}, test_mode={test_mode}")

    def log_work_session(self, task, files_changed=None, error_details=None, execution_time=None, outcome=None):
        """Logs a structured work session entry."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        log_entry = {
            "timestamp": timestamp,
            "task": task,
            "files_changed": files_changed or [],
            "error_details": error_details or "None",
            "execution_time": f"{execution_time:.2f}s" if execution_time else "N/A",
            "outcome": outcome or "N/A"
        }

        # Store log in ChromaDB
        self.collection.add(
            ids=[timestamp],
            documents=[json.dumps(log_entry)]
        )

        # Format for Markdown
        markdown_entry = f"## [{timestamp}] {task}\n"
        markdown_entry += f"- **Files Changed:** {', '.join(log_entry['files_changed'])}\n"
        markdown_entry += f"- **Errors Encountered:** {log_entry['error_details']}\n"
        markdown_entry += f"- **Execution Time:** {log_entry['execution_time']}\n"
        markdown_entry += f"- **Outcome:** {log_entry['outcome']}\n"

        # Append to Markdown file
        with open(self.session_log_file, "a") as f:
            f.write(markdown_entry + "\n")

        print(f"✅ Work session logged successfully: {task}")

    def log_ai_execution(self, function, *args, **kwargs):
        """
        Wraps an AI function execution to automatically log timing,
        success/failure, and any errors encountered.
        """
        start_time = time.time()
        try:
            result = function(*args, **kwargs)
            execution_time = time.time() - start_time
            self.log_work_session(
                task=f"AI executed {function.__name__}",
                execution_time=execution_time,
                outcome="Success"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_trace = traceback.format_exc()
            self.log_work_session(
                task=f"AI executed {function.__name__}",
                execution_time=execution_time,
                error_details=error_trace,
                outcome="Failed"
            )
            return None

    def retrieve_recent_sessions(self, hours=1):
        """Retrieves work session logs from the past `hours` by parsing the Markdown file."""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)

        try:
            with open(self.session_log_file, "r") as f:
                logs = f.readlines()
        except FileNotFoundError:
            print("⚠ No previous work sessions found.")
            return []

        recent_logs = []
        for line in logs:
            if line.startswith("## ["):
                timestamp_str = line.split("[")[1].split("]")[0]
                log_time = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                if log_time >= cutoff_time:
                    recent_logs.append(line.strip())

        return recent_logs

# Example usage
if __name__ == "__main__":
    logger = WorkSessionLogger(test_mode=False)

    def sample_ai_task():
        time.sleep(1)
        return "AI completed task successfully."

    logger.log_ai_execution(sample_ai_task)
    logger.log_work_session(
        task="Refactored AI work session logging",
        files_changed=["work_session_logger.py", "query_chroma.py"],
        error_details="None",
        execution_time=1.23,
        outcome="Successfully refactored AI logging."
    )
