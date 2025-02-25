# AI Recall System - Testing Plan

## 1. Overview

This document describes the **test suite** for the AI Recall System. Our goals are to:

- Verify that **blueprint execution** logic works correctly (e.g., triggers or skips revision proposals).
- Ensure **agent manager** communicates with the local LLM(s) properly (no offline mocking).
- Confirm that **ChromaDB** retrieval logic (via `query_chroma.py`) functions as expected.
- Keep our test environment "clean" using **ephemeral Chroma** directories, so test data does not pollute production logs.

We focus on **real** LLM calls and **real** Chroma usage (no mocks), which is important for capturing genuine system behavior.

---

## 2. Test Directory & Structure

All test scripts reside in:
/mnt/f/projects/ai-recall-system/tests/

Currently, we have three key files:

1. **`test_blueprint_execution.py`**  
   - Thorough tests for the `BlueprintExecution` class (located in `scripts/blueprint_execution.py`).
   - Covers catastrophic fails, ratio-based triggers, single-run success, LLM fallback, etc.

2. **`test_agent_manager.py`**  
   - Tests for `AgentManager` (found in `code_base/agent_manager.py`).
   - Checks real calls to the local LLM, handling timeouts, delegate tasks, preprocessor calls, etc.

3. **`test_query_chroma.py`**  
   - Tests the retrieval scripts in `scripts/query_chroma.py`.
   - Ensures we can store and retrieve logs, proposals, etc., from a fresh Chroma DB.

We’ll likely add more as the system expands.

---

## 3. Environment Setup

1. **Python environment**  
   - Ensure you have a working Python environment (e.g., `py310_env`) with `pytest` installed:

     ```bash
     pip install pytest
     ```

2. **LM Studio & Model**  
   - Spin up LM Studio, load your model(s) (Deepseek Coder 33B, etc.).
   - Ensure your `api_structure.py` or agent code is running on Flask if needed.  
   - Double-check that your system auto-detects WSL and the IP is correct (172.17.128.1).

3. **ChromaDB**  
   - Typically runs in the same environment. Our tests create **temporary** directories for ephemeral usage, so no special steps are needed. Just ensure you can read/write to `/tmp/` or similar.

---

## 4. Running the Tests

1. **Navigate to** the project root:

   ```bash
   cd /mnt/f/projects/ai-recall-system

Run Pytest:

bash
Copy
Edit
pytest -v --maxfail=1 tests
-v (verbose) shows each test name.
--maxfail=1 stops at the first failing test, so you can debug quickly. Omit this if you want to see the entire suite’s results.
Outputs

You’ll see lines like:
bash
Copy
Edit
============================= test session starts =============================
...
test_blueprint_execution.py::test_successful_run_no_revision PASSED
test_blueprint_execution.py::test_catastrophic_run_triggers_revision PASSED
...
============================== 8 passed in 3.47s ==============================
A “PASSED” result means each scenario was satisfied.
If a test fails, Pytest will display an error and possibly a traceback.
5. Tests Breakdown & Expected Outputs
5.1 test_blueprint_execution.py
This suite covers:

Ephemeral Chroma Setup

We create a temp directory so logs and proposals go into a fresh DB. At the end, we remove it, preventing “junk data” from mixing with real logs.
Success-Only Runs

e.g., test_successful_run_no_revision():
We log a run with success=True, efficiency=80.
We expect no blueprint revision in the revision_proposals collection for that blueprint.
Catastrophic Fails

e.g., test_catastrophic_run_triggers_revision():
We log a run with efficiency_score=20 (and possibly meltdown text).
Expect an immediate revision. We confirm an entry in revision_proposals with “catastrophic fail” in the notes.
Ratio Approach

e.g., test_ratio_run_triggers_revision():
We do multiple runs, with the second and third sub-threshold.
Expect a revision upon that third run. The stored proposal mentions “ratio check”.
LLM Fallback

e.g., test_llm_fallback():
We forcibly cause an LLM error (by mocking agent_manager.send_task).
Confirm the fallback text is stored in “improvement_notes.”
For real usage, you might skip this or do a smaller mock approach.
Expected Output:

Each test that triggers a revision will show “PASSED” if it finds the revision proposals.
If a test scenario is not met, you’ll see a Pytest failure with details.
5.2 test_agent_manager.py
Focuses on:

Live LLM Calls

test_send_task_success(): We send a basic prompt to “engineer.” Expect a non-empty string.
If the model or Flask API is down, we’ll see a request error.
Timeout Handling

test_send_task_timeout(): We pass a very short timeout=0.001. The result should contain “Timeout” or ❌ message.
Delegate Task

We ensure if the first attempt returns empty, it tries a second with stricter formatting. We do minimal mocking or real approach.
Preprocessor

test_preprocessor(): We call preprocess_ai_response() with some text and see if we get code (like “def …”).
Expected Output:

The tests pass if the LLM is running and responding.
If your model is slow or your timeouts are too tight, you might get a fail. That’s fine—adjust if needed or skip some tests in CI if the environment is not guaranteed to have a fast model.
5.3 test_query_chroma.py
Covers:

Storing & Retrieving from ephemeral Chroma.
list_execution_logs() verifying minimal printed output.
get_past_execution_attempts(...) ensuring it returns the correct doc.
Expected Output:

We insert a doc.
We call the retrieval function.
If it sees that doc, test passes.
If it prints or logs correct summary, it’s working as intended.
6. Evaluating Results
All Tests Pass:

You see a final summary like “8 passed in 3.47s.”
This means your pipeline is stable for the tested scenarios.
Failures:

Pytest shows a stack trace and test name. Investigate your code or environment.
Check if your LLM or Flask server was offline, or if the ephemeral DB path was unwritable, etc.
Edge Cases:

If you want to see how each test handles edge inputs (like negative efficiency, or missing fields), add more test functions.
Keep consistent with the ephemeral approach so you don’t store partial logs in your real “production” Chroma data.
7. Keeping a Clean Chroma Database
We rely on:

fresh_chroma_dir fixture in test_blueprint_execution.py and test_query_chroma.py.
Creates a temp dir (tempfile.mkdtemp(prefix="chroma_test_")).
After each test or test session, it’s removed.
This ensures no leftover logs or proposals pollute future tests or your real environment.

By following these test scripts, ephemeral DB usage, and running pytest with a live LLM & local Chroma, you achieve:

High coverage of your blueprint logic, LLM usage, and Chroma retrieval.
Minimal risk of leftover data mixing with real logs.
Confidence in each pipeline stage (logging → thresholds → revision → LLM-based improvements).
Happy testing!
