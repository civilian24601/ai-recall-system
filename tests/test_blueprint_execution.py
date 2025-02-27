import os
import pytest
import json
import chromadb

from code_base.agent_manager import AgentManager
from scripts.blueprint_execution import BlueprintExecution

@pytest.fixture(scope="module")
def test_chroma_client():
    """
    Creates a single Chroma client for this module's tests.
    We'll re-use it for ephemeral test collections if needed.
    """
    client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
    yield client
    # (No global teardown needed unless you want to wipe test collections completely.)

@pytest.fixture
def blueprint_exec(test_chroma_client):
    """
    Creates a BlueprintExecution with test_mode=True, meaning it will write to:
      - execution_logs_test
      - blueprint_versions_test
      - blueprint_revisions_test

    We'll also remove any existing docs in those test collections before/after each test
    by retrieving all doc IDs, then deleting by ID.
    """
    # We can pass a dummy or real AgentManager if needed
    agent_mgr = AgentManager()  # or None if you don't want LLM calls

    be = BlueprintExecution(agent_manager=agent_mgr, test_mode=True)

    # ---- Clean up these test collections before each test run ----
    _delete_all_docs(be.execution_logs)
    _delete_all_docs(be.blueprint_versions)
    _delete_all_docs(be.revision_proposals)

    yield be

    # ---- Clean up again after the test runs ----
    _delete_all_docs(be.execution_logs)
    _delete_all_docs(be.blueprint_versions)
    _delete_all_docs(be.revision_proposals)

def _delete_all_docs(collection):
    """
    Helper: fetch all docs in the given collection (with a large limit),
    then delete them by IDs. This avoids passing an empty 'where' filter,
    which newer Chroma versions disallow.
    """
    # Get up to 10k docs; adjust if your test data might exceed that
    results = collection.get(limit=10000)
    if "ids" in results and results["ids"]:
        all_ids = results["ids"]
        collection.delete(ids=all_ids)


def test_normal_above_threshold(blueprint_exec):
    """
    Scenario 1:
    - success=True, efficiency_score=80 => above default threshold (70).
    => No blueprint revision triggered.
    """
    _ = blueprint_exec.log_execution(
        blueprint_id="bp_001",
        task_name="Test Normal Pass",
        execution_context="Just a normal scenario",
        expected_outcome="Should pass threshold, no meltdown",
        execution_time=1.0,
        files_changed=["foo.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="None",
        success=True,
        efficiency_score=80,  # above the default threshold of 70
        improvement_suggestions="Everything is fine"
    )

    # Confirm no blueprint revision in blueprint_revisions_test
    res = blueprint_exec.revision_proposals.get(where={"blueprint_id": "bp_001"})
    # If empty => no revision triggered
    assert not res["documents"], "Expected no revision doc, but found some!"

def test_catastrophic_meltdown(blueprint_exec):
    """
    Scenario 2:
    - meltdown phrase or efficiency_score < 30 => immediate revision
    => We expect a doc in blueprint_revisions_test
    """
    _ = blueprint_exec.log_execution(
        blueprint_id="bp_002",
        task_name="Test Catastrophic",
        execution_context="We have meltdown error",
        expected_outcome="Should trigger meltdown approach",
        execution_time=2.5,
        files_changed=["bar.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="Catastrophic meltdown: index out of range",
        success=False,
        efficiency_score=20,  # below the catastrophic threshold of 30
        improvement_suggestions="Needs immediate fix"
    )

    res = blueprint_exec.revision_proposals.get(where={"blueprint_id": "bp_002"})
    # We expect exactly 1 doc
    assert len(res["documents"]) == 1, "Expected exactly 1 blueprint revision for meltdown scenario."

    rev_data = json.loads(res["documents"][0])
    assert "revision_id" in rev_data, "Revision doc is missing revision_id."
    assert "improvement_notes" in rev_data, "Revision doc is missing improvement_notes."
    # We expect meltdown mention in improvement notes
    notes_lower = rev_data["improvement_notes"].lower()
    assert "catastrophic" in notes_lower or "meltdown" in notes_lower, \
        "Expected meltdown mention in improvement notes."

def test_repeated_subthreshold(blueprint_exec):
    """
    Scenario 3:
    - We do multiple calls:
      1) success=False, eff=60
      2) success=False, eff=65
      3) success=False, eff=65 => ratio approach triggers revision
    """
    # First run
    blueprint_exec.log_execution(
        blueprint_id="bp_003",
        task_name="Test Subthreshold Ratio",
        execution_context="First fail",
        expected_outcome="Should not meltdown alone",
        execution_time=1.5,
        files_changed=["baz.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="Some minor fail",
        success=False,
        efficiency_score=60,
        improvement_suggestions="Potential fix #1"
    )

    # Second run
    blueprint_exec.log_execution(
        blueprint_id="bp_003",
        task_name="Test Subthreshold Ratio",
        execution_context="Second fail",
        expected_outcome="Still no meltdown alone",
        execution_time=1.8,
        files_changed=["baz.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="Another minor fail",
        success=False,
        efficiency_score=65,
        improvement_suggestions="Potential fix #2"
    )

    # Third run => ratio approach triggers revision
    blueprint_exec.log_execution(
        blueprint_id="bp_003",
        task_name="Test Subthreshold Ratio",
        execution_context="Third call => triggers ratio fail",
        expected_outcome="We want to see ratio approach cause revision",
        execution_time=2.0,
        files_changed=["baz.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="Subthreshold again",
        success=False,
        efficiency_score=65,
        improvement_suggestions="Potential fix #3"
    )

    # Now we expect a blueprint revision doc
    res = blueprint_exec.revision_proposals.get(where={"blueprint_id": "bp_003"})
    assert len(res["documents"]) == 1, "Expected exactly 1 blueprint revision for repeated sub-threshold scenario."

    rev_data = json.loads(res["documents"][0])
    assert "improvement_notes" in rev_data, "Revision doc missing improvement_notes."

    # The reason_string includes "[Ratio check]" but it might be capitalized. 
    # We'll do a case-insensitive check for 'ratio check'.
    notes_lower = rev_data["improvement_notes"].lower()
    assert "ratio check" in notes_lower, "Expected ratio mention in improvement notes."
