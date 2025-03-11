import pytest
import os
import json
from io import StringIO
import chromadb

import scripts.query_chroma as qchroma

@pytest.fixture
def test_chroma():
    """
    Create a single Chroma client, 
    get the test collections for ephemeral usage.
    We'll assign them to qchroma.* global variables.
    """
    client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
    logs_test_coll = client.get_or_create_collection(name="execution_logs_test")
    yield logs_test_coll
    # Teardown
    results = logs_test_coll.get(limit=9999)
    if "ids" in results and results["ids"]:
        logs_test_coll.delete(ids=results["ids"])

@pytest.fixture
def patch_query_chroma(test_chroma):
    """
    We patch the query_chroma script's global 'execution_logs'
    so it references 'execution_logs_test' collection, not the real one.
    """
    qchroma.execution_logs = test_chroma
    yield
    # no teardown needed, the other fixture does it

def test_list_execution_logs(patch_query_chroma):
    """
    We add a doc in 'execution_logs_test', 
    then call qchroma.list_execution_logs() and capture the print output.
    """
    # Add a doc
    log_data = {
        "execution_trace_id": "abc123",
        "task_name": "Test Task",
        "success": True,
        "efficiency_score": 95
    }
    qchroma.execution_logs.add(
        ids=["log_abc123"],
        documents=[json.dumps(log_data)]
    )

    # Now capture output
    from _pytest.capture import CaptureFixture  # if you want to do inline
    import io
    import sys

    backup_stdout = sys.stdout
    try:
        sys.stdout = io.StringIO()
        qchroma.list_execution_logs(limit=10)
        printed = sys.stdout.getvalue()
    finally:
        sys.stdout = backup_stdout

    assert "Test Task" in printed, "Expected the task name in output."
    assert "abc123" in printed, "Expected the exec ID in output."
    assert "success=True" in printed, "Expected success field in the summary line."
