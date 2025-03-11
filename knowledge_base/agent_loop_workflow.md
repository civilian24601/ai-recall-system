### Revised Agent Flow: Universal Workflow
Added: March 7, 2025 10:51 AM

The AI Recall System’s agent flow is designed as a flexible, scalable pipeline to handle a broad spectrum of debug and fix scenarios—beyond just ZeroDivisionError and KeyError. It uses agent.py as a testing proxy, with plans to transition to multi_agent_workflow.py using debug_logs.json once validated. The synergy between agent.py, agent_manager.py, and blueprint_execution.py forms a robust framework, with BELogs (Blueprint Execution Logs) as a critical component for tracking, analysis, and evolution.

### Flow Overview

1. **Trigger**: agent.py (or future multi_agent_workflow.py) initializes with a state reset and loads unresolved errors from debug_logs_test.json (or debug_logs.json).
2. **Error Processing**: Iterates over errors, delegating to LLMs via agent_manager.py for fix generation and review.
3. **Task Execution**: Uses blueprint_execution.py to apply fixes via blueprints, validated against the error context.
4. **BELog Integration**: Records execution details in BELogs for real-time monitoring, post-mortem analysis, and blueprint evolution.
5. **Debug Update**: Updates debug_logs_test.json/debug_logs.json with resolution status.
6. **Termination**: Exits when all errors are resolved or max attempts are exhausted, resetting state.

### Synergy Breakdown

- **agent.py (Proxy)**: Orchestrates the workflow, testing the pipeline with single-agent logic. It will be replaced by multi_agent_workflow.py, which will handle parallel agent tasks for scalability.
- **agent_manager.py**: Manages LLM interactions (engineer and reviewer), ensuring task-specific prompts and responses are processed consistently across any error type.
- **blueprint_execution.py**: Executes predefined tasks (e.g., "Apply fix", "Validate fix") from blueprints, staging changes and validating outcomes for any debug scenario.

### Engineer and Reviewer Flow (Universal)

- **Engineer**: Generates an initial fix for any error (e.g., TypeError, FileNotFoundError) based on script context and error details.
- **Reviewer**: Refines the fix, ensuring adherence to coding standards (e.g., proper exception handling, no side effects) for any issue.
- **Integration**: final_fix is set to the reviewer’s output if valid; otherwise, the engineer’s fix is used, adaptable to diverse error cases.

### Blueprint and Debug Integration

- **Blueprints**: Define reusable task sequences (e.g., "Apply fix", "Rollback on failure") with expected outcomes, executed by blueprint_execution.py for any fix scenario.
- **Debug Logs**: Track error state, fix attempts, and resolution in debug_logs_test.json (test) or debug_logs.json (production), driving the loop and supporting multi-agent scaling.

### BELogs Role

BELogs (Blueprint Execution Logs) are the system’s memory and audit trail, stored in the execution_logs Chroma collection. They:

- **Record**: Timestamp, task name, script path, success/failure, efficiency score, and improvement suggestions for every blueprint execution.
- **Analyze**: Enable post-mortem debugging (e.g., why a fix failed) and performance tracking (e.g., efficiency thresholds).
- **Evolve**: Trigger blueprint version updates (e.g., bp_fix_test1_v2.1) when improvements are suggested, adapting to new error patterns.

---

### Systematized Formula for Universal Workflow

Codify this in ai_coding_guidelines.md under a "Universal Agent Workflow Standard" section. This formula is agnostic to specific errors, applicable to any debug scenario, and includes BELogs’ role:

### Formula: Universal AI Recall System Agent Workflow

text

CollapseWrapCopy

`WORKFLOW = INIT_STATE → ERROR_LOOP(ENGINEER_TASK → REVIEW_TASK → BLUEPRINT_TASK(BELOG)) → UPDATE_LOGS → TERMINATE`

- **INIT_STATE**:
    - **Action**: agent.py (or multi_agent_workflow.py) resets scripts and debug_logs_test.json/debug_logs.json to initial state.
    - **Expected State**: All scripts contain original code; logs list unresolved errors (e.g., {"id": "err123", "error": "TypeError", "resolved": false}) from test or production sources.
    - **Script Reference**: agent.py.reset_state() or equivalent in multi_agent_workflow.py.
    - **Context Needed**: Script paths, log file location (provide if dynamic).
- **ERROR_LOOP**:
    - **Action**: Iterate over unresolved errors until resolved or max_attempts (5) reached, supporting parallel processing in multi_agent_workflow.py.
    - **Sub-Process**: ENGINEER_TASK → REVIEW_TASK → BLUEPRINT_TASK(BELOG).
    - **Expected State**: Each error triggers a fix attempt, adaptable to any error type (e.g., ValueError, IOError).
    - **Context Needed**: Error detection mechanism (e.g., stack traces from logs).
- **ENGINEER_TASK**:
    - **Action**: agent.py calls agent_manager.delegate_task("engineer", prompt) with error and script context.
    - **Prompt**: e.g., "Debug script with error [error_type] at [stack_trace], return only fixed function with try/except for [error_type]."
    - **Output**: fix (e.g., def process_data(x): try: return x["key"] except KeyError: return None for KeyError).
    - **Expected State**: fix is a valid Python function with try/except for the specific error, regardless of type.
    - **Script Reference**: agent_manager.py.send_task(), agent.py task prompt logic.
- **REVIEW_TASK**:
    - **Action**: agent.py calls agent_manager.delegate_task("reviewer", prompt) with fix.
    - **Prompt**: e.g., "Review [fix], ensure it handles [error_type] with try/except, return only refined function."
    - **Output**: reviewed_fix (should match or improve fix).
    - **Expected State**: reviewed_fix is valid; if invalid, final_fix defaults to fix. Applies to any error (e.g., SyntaxError, TimeoutError).
    - **Script Reference**: agent_manager.py.send_task(), agent.py review logic.
    - **Context Needed**: Reviewer LLM’s capability to handle diverse errors (provide model details if unique).
- **BLUEPRINT_TASK(BELOG)**:
    - **Action**: agent.py calls blueprint_execution.run_blueprint("Apply fix", script_path, final_fix, original_error).
    - **Process**: Stages final_fix in a temp file, validates with test_fix(), applies if successful, logs to BELog.
    - **BELog Details**:
        - **Record**: {"timestamp": "YYYY-MM-DD HH:MM:SS", "task_name": "Apply fix", "script_path": "[path]", "success": true/false, "efficiency_score": [0-100], "improvement_suggestions": "[notes]"}.
        - **Analyze**: Tracks execution time, success rate, and failure reasons for any task.
        - **Evolve**: Updates blueprint version (e.g., bp_fix_err123_v2.1) if success = false with suggestions.
    - **Output**: Updated script if validated; BELog entry regardless of outcome.
    - **Expected State**: Script contains final_fix; BELog reflects execution (e.g., success: true for valid fix, improvement_suggestions: "Add logging" for failure).
    - **Script Reference**: blueprint_execution.py.run_blueprint(), blueprint_execution.py.log_execution().
    - **Context Needed**: Blueprint file structure (provide agent_blueprint_v1.json if dynamic).
- **UPDATE_LOGS**:
    - **Action**: agent.py updates debug_logs_test.json/debug_logs.json with resolved = test_fix_result.
    - **Expected State**: Logs reflect resolved: true for fixed errors, with fix, test_result, and execution_trace_id for any error type.
    - **Script Reference**: agent.py.log_entry(), debug_logs_test.json write.
    - **Context Needed**: Log schema (provide if varies from test to production).
- **TERMINATE**:
    - **Action**: agent.py (or multi_agent_workflow.py) exits when no unresolved errors or max_attempts reached, resets state.
    - **Expected State**: All errors resolved or logged as failed; scripts and logs reset for next run.
    - **Script Reference**: agent.py.reset_state() or equivalent.
    - **Context Needed**: Reset behavior for production (e.g., backup strategy).

### Constraints

- **Max Attempts**: 5 per error, adjustable for production.
- **Validation**: test_fix() must simulate the original error context (e.g., divide(10, 0) for ZeroDivisionError).
- **Final Fix**: final_fix = reviewed_fix if valid; else fix if valid; else None.
- **BELog Thresholds**: Efficiency ≥ 70, Catastrophic ≤ 30 (tunable).

### Example State (Universal)

- **Input**: debug_logs.json = [{"id": "err123", "error": "FileNotFoundError", "stack_trace": "File 'data.txt', line 5", "resolved": false}].
- **Process**: ENGINEER_TASK → fix = def read_file(path): try: with open(path) except FileNotFoundError: return None; REVIEW_TASK → reviewed_fix = same; BLUEPRINT_TASK(BELOG) → applies fix, BELog = {"success": true, "efficiency_score": 85}; UPDATE_LOGS → {"resolved": true, "fix": "..."}.
- **Output**: Script updated; BELog and logs reflect resolution.

---

### Applicability to Universal Issues

This workflow is designed for any debug scenario:

- **Error Agnostic**: Handles SyntaxError, TimeoutError, MemoryError, etc., by adapting prompts and validation to the error type.
- **Scalable**: multi_agent_workflow.py can parallelize tasks for multiple errors, leveraging the same structure.
- **BELog-Driven**: Evolution and analysis adapt to new error patterns, ensuring robustness.

UPDATE March 8 2025 -
    Problems with using Regex in our engineer/reviewer pipeline:
    Unusability for an AI Build Engine
You’re correct that this makes the current solution unsuitable for a general-purpose "AI build engine" tasked with triaging and fixing any size or shape of code. An engine like that needs:

Error Localization: Ability to pinpoint the exact function or line causing the error from the stack_trace.
Modular Fixes: Capacity to apply fixes to specific sections (e.g., a function, a class method, or global code) without rewriting the entire script.
Scalability: Handling large files with complex structures (nested functions, classes, decorators) and diverse error types.
Robust Parsing: Tolerance for varied formatting (tabs, mixed indentation, inline bodies) and edge cases.
The regex approach, while useful for prototyping, is too rigid and error-prone for these requirements. It’s a good choice for a controlled, narrow use case but falls apart as the codebase grows or diversifies.