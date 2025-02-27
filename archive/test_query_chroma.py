import pytest
import os
import sys
import shutil
import tempfile
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
# So we can import query_chroma.py from /scripts
sys.path.append(os.path.join(PARENT_DIR, "scripts"))

import chromadb

# We'll import query_chroma but also patch out PersistentClient so it uses ephemeral path
import importlib

@pytest.fixture
def fresh_chroma_dir():
    """
    Creates a fresh temporary directory for Chroma. 
    The ephemeral tests won't mix with real logs.
    """
    temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def ephemeral_query_module(fresh_chroma_dir):
    """
    Dynamically reloads query_chroma.py with a monkey-patch that sets a custom path for chromadb.
    This ensures ephemeral usage. 
    We'll also store references to ephemeral collections within query_chroma.
    """
    import chromadb

    # Keep the original PersistentClient
    original_client = chromadb.PersistentClient

    def patched_client(*args, **kwargs):
        new_kwargs = dict(kwargs)
        # Force usage of the ephemeral path from our fixture
        new_kwargs["path"] = fresh_chroma_dir
        return original_client(*args, **new_kwargs)

    # Patch
    old_persistent_client = chromadb.PersistentClient
    chromadb.PersistentClient = patched_client

    # Now import or reload query_chroma
    import query_chroma
    importlib.reload(query_chroma)

    yield query_chroma

    # revert the monkey-patch
    chromadb.PersistentClient = old_persistent_client
    importlib.reload(query_chroma)


def test_list_execution_logs(ephemeral_query_module):
    """
    We'll insert minimal logs into ephemeral DB, then call ephemeral_query_module.list_execution_logs().
    We'll do minimal checks, ensuring no path usage. 
    We won't parse the console output unless we want to test capsys.
    """
    # ephemeral_query_module has "execution_logs = chroma_client.get_or_create_collection(name='execution_logs')"
    # so let's reference ephemeral_query_module.execution_logs
    exec_collection = ephemeral_query_module.execution_logs

    doc_str = json.dumps({
        "execution_trace_id": "log_test_123",
        "task_name": "Test QueryChroma",
        "success": True,
        "efficiency_score": 88
    })
    exec_collection.add(
        ids=["log_test_123"],
        documents=[doc_str],
        metadatas=[{
            "task_name": "Test QueryChroma",
            "efficiency_score": 88,
            "success": True
        }]
    )

    # Now call ephemeral_query_module.list_execution_logs() 
    ephemeral_query_module.list_execution_logs()

    # Minimal check: confirm we have 1 doc
    results = exec_collection.get(limit=10)
    assert results and len(results["documents"]) == 1, "Expected 1 doc in ephemeral DB"


def test_get_past_execution_attempts(ephemeral_query_module):
    """
    We'll add a doc for a known 'task_name', then call ephemeral_query_module.get_past_execution_attempts
    and ensure it returns it. 
    """
    exec_collection = ephemeral_query_module.execution_logs

    doc_str = json.dumps({
        "execution_trace_id": "log_test_456",
        "task_name": "Another Task",
        "success": False,
        "efficiency_score": 50
    })
    exec_collection.add(
        ids=["log_test_456"],
        documents=[doc_str],
        metadatas=[{
            "task_name": "Another Task",
            "efficiency_score": 50,
            "success": False
        }]
    )

    # Now we call ephemeral_query_module.get_past_execution_attempts
    attempts = ephemeral_query_module.get_past_execution_attempts("Another Task", limit=5)

    assert len(attempts) == 1, "Should find exactly 1 doc with that task_name"
    assert attempts[0]["execution_trace_id"] == "log_test_456"
    assert attempts[0]["efficiency_score"] == 50
    assert attempts[0]["success"] == False
