TEST_SCENARIOS.md
Overview
This document outlines each major test scenario—its purpose, inputs, expected result, and fallback steps if something goes wrong. By enumerating these clearly, we ensure our tests remain consistent, traceable, and easily referenced by humans or AI.

Table of Contents
Scenario 1: DebugStrategy - Basic Logs
Scenario 2: DebugStrategy - Duplicate Snippets
Scenario 3: BlueprintExecution - Normal Above Threshold
Scenario 4: BlueprintExecution - Catastrophic Fail
Scenario 5: WorkSessionLogger - AI Exception Wrap
Scenario 6: Integration - Code Index + Aggregator
Scenario 7: Integration - BFS Flow (Multi-Agent)
Scenario 8: Edge: Large debug_logs with 500 entries
Manual Reassurance Checklist

Scenario 1: DebugStrategy - Basic Logs
Category Unit (debugging_strategy.py)
Prerequisites debug_logs_small.json (3–5 entries, success/fail mix)
Steps 1. Copy debug_logs_small.json into /logs/ or point the script to /tests/mock_data/debug_logs/debug_logs_small.json.
2. Run python debugging_strategy.py.
3. Observe console output.
Expected Result - The script processes each log entry without error.

- Creates/updates strategies in debugging_strategy_log.json.
- No meltdown or skip needed.
Fallback - If it raises JSON decode errors, confirm you used the correct JSON file (not corrupt).
- If success rates remain at 0, check your snippet normalization or success logic.
Notes This is a basic test ensuring the strategy logs are updated properly with a small dataset.

Scenario 2: DebugStrategy - Duplicate Snippets
Category Unit (debugging_strategy.py)
Prerequisites debug_logs_medium.json (with repeated near-identical fix_attempted snippets).
Steps

1. Copy debug_logs_medium.json or point the script to it.
2. Run python debugging_strategy.py.
3. Inspect debugging_strategy_log.json for multiple or single entries.
Expected Result - Duplicate or near-identical snippets unify into one strategy (thanks to normalization).

- Success rates reflect combined attempts.
Fallback - If it’s creating multiple duplicates, confirm the normalize_snippet() logic.
- If it errors out, verify you’re not missing fields.
Notes Ensures snippet normalization merges repeated fix_attempted strings.
Scenario 3: BlueprintExecution - Normal Above Threshold
Category Unit (blueprint_execution.py)
Prerequisites - Minimal execution_logs_small.json with success≥80% logs.
Steps 1. Make sure the script references your test Chroma collections (or mock logs).

2. Run a normal success scenario: python blueprint_execution.py or call log_execution(...) with success=80.
Expected Result - No blueprint revision triggered.

- A new execution log entry is stored in execution_logs.
Fallback - If meltdown triggers, confirm you used the success≥80 scenario.
- If it logs a blueprint revision, check if your thresholds were set properly.
Notes Basic “happy path” test ensuring no meltdown or ratio-based fail.
Scenario 4: BlueprintExecution - Catastrophic Fail
Category Unit (blueprint_execution.py)
Prerequisites - Same execution_logs_small.json, but includes a meltdown phrase or efficiency=20.
Steps 1. Insert or run log_execution(...) with success=False, errors containing meltdown phrase.

2. Check the console for “Blueprint Revision Triggered.”
Expected Result - Logs a new attempt with eff=20, meltdown phrase.

- Immediately triggers generate_blueprint_revision(...).
- A revision doc appears in blueprint_revisions.
Fallback - If no revision is triggered, verify meltdown phrases match your script.
- If it errors out, confirm agent_manager is optional or pass it as None.
Notes Confirms meltdown logic properly spawns a revision proposal.
Scenario 5: WorkSessionLogger - AI Exception Wrap
Category Unit (work_session_logger.py)
Prerequisites - A function that intentionally raises ValueError or ZeroDivisionError.
Steps 1. In a small script, do logger.log_ai_execution(faulty_function).

2. Observe .md file and Chroma for “Errors Encountered.”
Expected Result - The logger wraps the call, logs an error stack trace, outcome=“Failed.”

- No meltdown or skip needed, just verifying error details.
Fallback - If it logs success, check that your exception was truly raised.
- If no entry is appended, confirm the function is actually called.
Notes Ensures that an AI-executed function that fails is recorded with error details.
Scenario 6: Integration - Code Index + Aggregator
Category Integration
Prerequisites - mini_project/ or medium_project/ in /tests/mock_data/codebase/.
- index_codebase.py script referencing that folder.
Steps 1. Run python index_codebase.py --path /tests/mock_data/codebase/mini_project/.

2. Then python aggregator_search.py "mock" 3.
3. Confirm aggregator finds references to “mock.”
Expected Result - The codebase is chunked and embedded into project_codebase_test (or similar).

- Aggregator returns relevant chunks for “mock.”
Fallback - If dimension mismatch or meltdown error, check embedding model consistency.
- If aggregator returns zero matches, verify you typed the query string or path correctly.
Notes Basic check that code chunking + aggregator searching works end-to-end with mock code.
Scenario 7: Integration - BFS Flow (Multi-Agent)
Category Integration
Prerequisites - debug_logs_small.json or medium with an unresolved error.
- multi_agent_workflow.py if you have that script.
Steps 1. Run python multi_agent_workflow.py.

2. Check console for fix suggestions.
3. Confirm it updates the logs to “resolved.”
Expected Result - A fix is proposed, partial meltdown or meltdown phrase is updated as resolved.

- Possibly triggers blueprint revision if meltdown.
Fallback - If no fix is suggested, confirm the script found the right error in logs.
- If meltdown reoccurs, check your thresholds.
Notes End-to-end scenario verifying multi-agent retrieval, debugging, logging updates.
Scenario 8: Edge: Large debug_logs with 500 entries
Category Edge / Stress
Prerequisites - debug_logs_large.json (50–500 entries).
- debugging_strategy.py.
Steps 1. Replace or point your script to debug_logs_large.json.

2. python debugging_strategy.py.
3. Observe performance.
Expected Result - It processes all logs without timing out or meltdown.

- debugging_strategy_log.json updated with correct success rates.
Fallback - If it’s very slow or crashes, consider splitting the logs or verifying snippet normalization.
- If meltdown triggers, confirm your meltdown phrases.
Notes Tests performance on big logs. Ensures no out-of-memory or slow parsing.

Manual Reassurance Checklist
Before letting the AI or your blueprint system run these tests autonomously, do a manual pass to confirm everything is stable:

Check Chroma Connections

Does your test environment (or initialize_chroma.py) create separate test collections (e.g. execution_logs_test, debug_logs_test)?
If so, ensure your scripts reference them, not your “production” or real data.
Verify Each Script

debugging_strategy.py → run with small + medium logs. Confirm no errors.
blueprint_execution.py → test normal pass + meltdown. Confirm a blueprint revision if meltdown.
work_session_logger.py → test log_ai_execution(...). Confirm the .md file updates.
Look at the Output

For meltdown triggers, do you see the meltdown phrase in logs?
For ratio checks, do you see the correct threshold logic?
File Structure

Confirm your /tests/mock_data/ is correct and your scripts can find it.
Double-check .gitignore so you don’t accidentally commit large or temporary data.
Manual Pass

If everything passes your scenario doc (the table above), you have a green light to set up partial or full autonomy.
