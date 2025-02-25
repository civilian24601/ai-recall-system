# pipeline_review.md

```markdown
Blueprint Execution Pipeline Overview
Task Execution & Logging

Whenever the AI or human triggers a new task, we call blueprint_execution.log_execution(...).
Logs relevant metadata: task_name, success, efficiency_score, etc.
Stores a JSON doc plus key metadata fields in ChromaDB (execution_logs collection).
Thresholds & Checks

BlueprintExecution checks each run against two thresholds:
Catastrophic: extremely low efficiency_score or meltdown phrases in errors.
Ratio-based: we consider the last N runs (default N=3). If ≥ X are “bad” (fail/sub-threshold) or average efficiency < threshold, it triggers a revision.
LLM-Generated Improvement Notes

If triggered, we call build_llm_improvement_notes(...), feeding:
The reason (catastrophic or ratio check),
Summaries of recent runs,
A refined prompt telling the LLM to produce bullet-point suggestions.
The result is appended to improvement_notes.
Blueprint Revision Proposal

generate_blueprint_revision(...) is called, storing an entry in blueprint_revisions collection with the new “improvement_notes,” timestamp, and status “Pending Review.”
(Optional) Blueprint Versions

We can store or update blueprint_versions if a revision is approved. Over time, you might re-check logs referencing (blueprint_id, blueprint_version) to measure success rates and update the version’s “score.”
Reading & Debugging

You can run query_chroma.py to see short summaries of logs, revision proposals, etc.
blueprint_execution.get_past_attempts(...) prints a short summary of relevant logs, letting you debug each step.

```
