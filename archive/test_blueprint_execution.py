import pytest
import os
import shutil
import tempfile
import json

# We'll fix the path so we can import blueprint_execution + agent_manager from your code_base/scripts
import sys
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(PARENT_DIR + "/scripts")
sys.path.append(PARENT_DIR + "/code_base")

from agent_manager import AgentManager
from blueprint_execution import BlueprintExecution


@pytest.fixture
def fresh_chroma_dir():
    """
    Creates a fresh temporary directory for Chroma, so that each test run
    doesn't pollute the main DB with test data. We'll pass this path to
    the blueprint execution instance. After tests, we remove it.
    """
    temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
    yield temp_dir
    # Cleanup after tests
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def agent_mgr():
    """
    Creates an AgentManager instance for testing. We can mock or real.
    For now, let's create a real instance that points to your running LM Studio.
    If you want to mock the LLM, you can do so by monkey-patching agent_mgr.send_task.
    """
    return AgentManager()

@pytest.fixture
def blueprint_exec(agent_mgr, fresh_chroma_dir):
    """
    Creates a BlueprintExecution instance pointing to an ephemeral Chroma DB path.
    This ensures each test run is "clean."
    """
    # We'll override the path to Chroma by environment variable or monkey-patching.
    # But let's do it with a slight hack: We'll rename the constructor to accept a path if you'd like.
    # Alternatively, we can do a monkeypatch, but let's do the simplest approach:
    class EphemeralBlueprintExecution(BlueprintExecution):
        def __init__(self, agent_manager, path_to_chroma):
            # We'll call super init, then override the path
            super().__init__(agent_manager=agent_manager)
            # Now we re-init the chroma_client with a new path
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=path_to_chroma)
            self.execution_logs = self.chroma_client.get_or_create_collection(name="execution_logs")
            self.blueprint_versions = self.chroma_client.get_or_create_collection(name="blueprint_versions")
            self.revision_proposals = self.chroma_client.get_or_create_collection(name="blueprint_revisions")

    # return an ephemeral instance
    return EphemeralBlueprintExecution(agent_mgr, fresh_chroma_dir)


def test_successful_run_no_revision(blueprint_exec):
    """
    Test a run that is fully successful and above thresholds => no revision triggered.
    """
    # override threshold for a specific task:
    blueprint_exec.thresholds_map["Test Task"] = {
        "efficiency_threshold": 75,
        "catastrophic_threshold": 25,
        "ratio_window": 3,
        "ratio_fail_count": 2
    }

    exec_id = blueprint_exec.log_execution(
        blueprint_id="bp_test",
        task_name="Test Task",
        execution_context="Check success path",
        expected_outcome="Should pass easily",
        execution_time=1.0,
        files_changed=[],
        dependencies=[],
        pipeline_connections=[],
        errors="None",
        success=True,
        efficiency_score=80,
        improvement_suggestions="N/A"
    )
    assert exec_id.startswith("log_")

    # We can also confirm no blueprint revision was stored
    # by checking the revision_proposals collection
    # We'll do a direct check on blueprint_exec.revision_proposals
    results = blueprint_exec.revision_proposals.get(limit=5)
    if results and "documents" in results and results["documents"]:
        # parse them
        for doc in results["documents"]:
            rev = json.loads(doc)
            # we expect no new rev for 'bp_test' unless something else triggered
            assert rev["blueprint_id"] != "bp_test", "No revision should be created for a purely successful run."

def test_catastrophic_run_triggers_revision(blueprint_exec):
    """
    If we do a catastrophic run (low efficiency < 25),
    we expect an immediate revision to be triggered.
    """
    blueprint_exec.thresholds_map["Catastrophic Task"] = {
        "efficiency_threshold": 75,
        "catastrophic_threshold": 25,
        "ratio_window": 3,
        "ratio_fail_count": 2
    }

    exec_id = blueprint_exec.log_execution(
        blueprint_id="bp_cat",
        task_name="Catastrophic Task",
        execution_context="Testing meltdown scenario",
        expected_outcome="Should fail drastically",
        execution_time=2.0,
        files_changed=[],
        dependencies=[],
        pipeline_connections=[],
        errors="Catastrophic meltdown: index out of range",
        success=False,
        efficiency_score=20,  # definitely below 25
        improvement_suggestions="N/A"
    )
    assert exec_id.startswith("log_")

    # Now we check that a revision was proposed
    results = blueprint_exec.revision_proposals.get(where={"blueprint_id": "bp_cat"}, limit=5)
    assert results and "documents" in results, "Expected revision docs"
    docs = results["documents"]
    assert len(docs) > 0, "Should have at least one revision doc"
    rev_entry = json.loads(docs[-1])  # get the last doc
    assert "revision_id" in rev_entry
    assert rev_entry["blueprint_id"] == "bp_cat"
    assert "catastrophic fail" in rev_entry["improvement_notes"].lower()

def test_ratio_run_triggers_revision(blueprint_exec):
    """
    If we do multiple sub-threshold runs, we expect the ratio approach to propose a revision.
    We'll do 2 out of 3 sub-threshold attempts.
    """
    blueprint_exec.thresholds_map["Ratio Task"] = {
        "efficiency_threshold": 75,
        "catastrophic_threshold": 25,
        "ratio_window": 3,
        "ratio_fail_count": 2
    }

    # log first attempt above threshold
    blueprint_exec.log_execution(
        blueprint_id="bp_ratio",
        task_name="Ratio Task",
        execution_context="First attempt success",
        expected_outcome="No revision expected",
        execution_time=1.2,
        files_changed=[],
        dependencies=[],
        pipeline_connections=[],
        errors="None",
        success=True,
        efficiency_score=80,
        improvement_suggestions="N/A"
    )

    # second attempt sub-threshold
    blueprint_exec.log_execution(
        blueprint_id="bp_ratio",
        task_name="Ratio Task",
        execution_context="Second attempt sub-threshold",
        expected_outcome="No revision if it's single sub-threshold",
        execution_time=1.2,
        files_changed=[],
        dependencies=[],
        pipeline_connections=[],
        errors="Minor error",
        success=False,
        efficiency_score=60,
        improvement_suggestions="N/A"
    )

    # third attempt also sub-threshold => triggers ratio approach
    exec_id_3 = blueprint_exec.log_execution(
        blueprint_id="bp_ratio",
        task_name="Ratio Task",
        execution_context="Third attempt sub-threshold => trigger ratio",
        expected_outcome="We expect a ratio-based revision",
        execution_time=1.4,
        files_changed=[],
        dependencies=[],
        pipeline_connections=[],
        errors="Some minor error",
        success=False,
        efficiency_score=60,
        improvement_suggestions="N/A"
    )
    assert exec_id_3.startswith("log_")

    # confirm revision
    results = blueprint_exec.revision_proposals.get(where={"blueprint_id": "bp_ratio"}, limit=5)
    assert results and "documents" in results
    docs = results["documents"]
    assert len(docs) > 0
    rev_entry = json.loads(docs[-1])
    assert "ratio check" in rev_entry["improvement_notes"].lower(), "Should mention ratio check."

def test_llm_fallback(blueprint_exec):
    """
    If the LLM times out or returns nothing, we fallback to minimal improvement notes.
    We can mock the agent_manager's send_task to force an error and see if we fallback.
    """
    # We'll do a simple patch
    original_send_task = blueprint_exec.agent_manager.send_task

    def mock_fail_send_task(agent, prompt, timeout=180):
        raise Exception("Mock LLM failure")

    blueprint_exec.agent_manager.send_task = mock_fail_send_task

    blueprint_exec.thresholds_map["LLM Fallback"] = {
        "efficiency_threshold": 75,
        "catastrophic_threshold": 25,
        "ratio_window": 3,
        "ratio_fail_count": 1
    }

    # One sub-threshold run => ratio triggers
    exec_id = blueprint_exec.log_execution(
        blueprint_id="bp_llmfallback",
        task_name="LLM Fallback",
        execution_context="Test LLM error => fallback",
        expected_outcome="We should see a fallback text in improvement notes",
        execution_time=1.5,
        files_changed=[],
        dependencies=[],
        pipeline_connections=[],
        errors="None",
        success=False,
        efficiency_score=60,
        improvement_suggestions="N/A"
    )
    assert exec_id.startswith("log_")

    # check if revision was generated with fallback text
    results = blueprint_exec.revision_proposals.get(where={"blueprint_id":"bp_llmfallback"}, limit=5)
    docs = results["documents"]
    rev_entry = json.loads(docs[-1])
    assert "(llm error" in rev_entry["improvement_notes"].lower(), "Should contain fallback notes"

    # restore the original method
    blueprint_exec.agent_manager.send_task = original_send_task
