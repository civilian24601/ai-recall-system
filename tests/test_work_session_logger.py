import os
import pytest
import json
import time
import datetime

from code_base.work_session_logger import WorkSessionLogger
import chromadb

@pytest.fixture
def session_logger():
    """
    Creates a WorkSessionLogger in test_mode=True so it writes to:
      - tests/test_logs/work_session_test.md
      - work_sessions_test collection
    We'll also remove any existing docs from 'work_sessions_test'
    and remove the markdown file after each test.
    """
    logger = WorkSessionLogger(test_mode=True)

    # Clear the test collection
    _delete_all_docs(logger.collection)

    # Clear the test markdown file
    test_markdown_path = "tests/test_logs/work_session_test.md"
    if os.path.exists(test_markdown_path):
        os.remove(test_markdown_path)

    yield logger

    # Teardown: remove docs + remove the file
    _delete_all_docs(logger.collection)
    if os.path.exists(test_markdown_path):
        os.remove(test_markdown_path)

def _delete_all_docs(collection):
    """
    Helper to remove all docs from the 'work_sessions_test' collection
    by ID, avoiding the 'where={}' error.
    """
    results = collection.get(limit=10000)
    if "ids" in results and results["ids"]:
        all_ids = results["ids"]
        collection.delete(ids=all_ids)

def test_log_work_session(session_logger):
    """
    Test manually logging a session with known data,
    then parse the test markdown to confirm it was appended.
    """
    session_logger.log_work_session(
        task="Test Manual Logging",
        files_changed=["foo.py", "bar.py"],
        error_details="No errors found",
        execution_time=2.34,
        outcome="All good"
    )

    # Check the doc in the test collection
    docs = session_logger.collection.get(limit=10)
    assert len(docs["documents"]) == 1, "Expected exactly 1 doc in the test collection."
    
    # Check the local test markdown file
    test_markdown_path = "tests/test_logs/work_session_test.md"
    with open(test_markdown_path, "r") as f:
        lines = f.read()
    
    assert "Test Manual Logging" in lines, "Task name not found in markdown file."
    assert "foo.py, bar.py" in lines, "File changes not found in markdown file."
    assert "No errors found" in lines, "Error details not found in markdown file."

def test_log_ai_execution_success(session_logger):
    """
    Test log_ai_execution with a successful function.
    """
    def dummy_ai_task():
        time.sleep(0.5)
        return "Success result"

    result = session_logger.log_ai_execution(dummy_ai_task)
    assert result == "Success result", "Expected the AI function to return success."

    # Check the doc
    docs = session_logger.collection.get(limit=10)
    assert len(docs["documents"]) == 1, "Should have exactly 1 doc logged."
    
    data = json.loads(docs["documents"][0])
    assert data["task"] == "AI executed dummy_ai_task"
    assert data["outcome"] == "Success"

def test_log_ai_execution_failure(session_logger):
    """
    Test log_ai_execution with a failing function that raises an exception.
    """
    def failing_task():
        time.sleep(0.2)
        raise ValueError("Simulated AI fail")

    result = session_logger.log_ai_execution(failing_task)
    assert result is None, "Expected None return after an exception."

    docs = session_logger.collection.get(limit=10)
    assert len(docs["documents"]) == 1, "Should have exactly 1 doc logged."

    data = json.loads(docs["documents"][0])
    assert data["task"] == "AI executed failing_task"
    assert data["outcome"] == "Failed"
    assert "ValueError" in data["error_details"]

def test_retrieve_recent_sessions(session_logger):
    """
    Test retrieving logs from last 1 hour by the markdown file approach.
    We'll log 2 sessions: one now, one 2 hours ago. The older one shouldn't appear.
    """
    # 1) A recent session
    session_logger.log_work_session(
        task="Recent session",
        files_changed=["x.py"],
        error_details="None",
        execution_time=0.5,
        outcome="Recent success"
    )

    # 2) Fake an older log entry (2 hours ago) by manually appending to the markdown
    test_markdown_path = "tests/test_logs/work_session_test.md"
    old_time = (datetime.datetime.now() - datetime.timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
    with open(test_markdown_path, "a") as f:
        f.write(f"## [{old_time}] Old session\n")
        f.write(f"- **Files Changed:** old_file.py\n")
        f.write(f"- **Errors Encountered:** None\n")
        f.write(f"- **Execution Time:** 0.30s\n")
        f.write(f"- **Outcome:** Old log\n\n")

    # Now retrieve past 1 hour
    recent_logs = session_logger.retrieve_recent_sessions(hours=1)
    assert len(recent_logs) == 1, f"Expected only the newly logged session, found: {recent_logs}"
    assert "Recent session" in recent_logs[0], "Expected 'Recent session' in the single retrieved log."
