#!/usr/bin/env python3
"""
Blueprint Execution Script with LLM-Generated Improvement Notes

File path:
  /mnt/f/projects/ai-recall-system/scripts/blueprint_execution.py
"""

import sys
import os

# --- Fix the import path so Python can find 'code_base.agent_manager' ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(PARENT_DIR)

# Now we can import from the code_base folder
from code_base.agent_manager import AgentManager

import chromadb
import datetime
import json
import traceback

class BlueprintExecution:
    """
    Manages Blueprint Execution Logs (BELogs), Blueprint Versions, and AI Self-Iteration.
    """

    def __init__(self, agent_manager=None, test_mode=False):  # [CHANGED] add test_mode=False
        """
        If test_mode=True, we write to test collections:
          execution_logs_test, blueprint_versions_test, blueprint_revisions_test
        Otherwise, we use production ones: execution_logs, blueprint_versions, blueprint_revisions
        """
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        
        # [NEW] choose test vs production collections
        if test_mode:
            self.execution_logs = self.chroma_client.get_or_create_collection(name="execution_logs_test")
            self.blueprint_versions = self.chroma_client.get_or_create_collection(name="blueprint_versions_test")
            self.revision_proposals = self.chroma_client.get_or_create_collection(name="blueprint_revisions_test")
        else:
            self.execution_logs = self.chroma_client.get_or_create_collection(name="execution_logs")
            self.blueprint_versions = self.chroma_client.get_or_create_collection(name="blueprint_versions")
            self.revision_proposals = self.chroma_client.get_or_create_collection(name="blueprint_revisions")

        # We'll store the agent_manager for LLM calls
        self.agent_manager = agent_manager
        self.test_mode = test_mode  # [NEW] keep track if we need it later

        # Dictionary to store specific thresholds for certain tasks or blueprint IDs
        self.thresholds_map = {}

        # Fallback defaults
        self.DEFAULT_EFFICIENCY_THRESHOLD = 70
        self.DEFAULT_CATASTROPHIC_THRESHOLD = 30
        self.DEFAULT_RATIO_WINDOW = 3
        self.DEFAULT_RATIO_FAIL_COUNT = 2

        print(
            "⚙️ [BlueprintExecution __init__] Default thresholds:\n"
            f"    Efficiency threshold: {self.DEFAULT_EFFICIENCY_THRESHOLD}\n"
            f"    Catastrophic threshold: {self.DEFAULT_CATASTROPHIC_THRESHOLD}\n"
            f"    Ratio window: {self.DEFAULT_RATIO_WINDOW}\n"
            f"    Ratio fail count: {self.DEFAULT_RATIO_FAIL_COUNT}\n"
            f"test_mode={test_mode}, so using "
            f"{'execution_logs_test, blueprint_versions_test, blueprint_revisions_test' if test_mode else 'execution_logs, blueprint_versions, blueprint_revisions'}\n"
            "To override these for certain tasks, fill in self.thresholds_map.\n"
            "LLM-based improvement notes are enabled if you pass an agent_manager.\n"
        )

    def log_execution(
            self,
            blueprint_id: str,
            task_name: str,
            execution_context: str,
            expected_outcome: str,
            execution_time: float,
            files_changed: list,
            dependencies: list,
            pipeline_connections: list,
            errors: str,
            success: bool,
            efficiency_score: int,
            improvement_suggestions: str
        ) -> str:
        """
        Logs AI task execution in BELogs with structured metadata (for exact filtering).
        Then checks thresholds and possibly triggers a blueprint revision.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execution_trace_id = f"log_{timestamp.replace(' ', '_')}"

        blueprint_version = self.get_latest_blueprint_version(blueprint_id)
        thresholds = self.get_thresholds_for_task(task_name)
        eff_thresh = thresholds["efficiency_threshold"]
        cat_thresh = thresholds["catastrophic_threshold"]
        ratio_window = thresholds["ratio_window"]
        ratio_fail_count = thresholds["ratio_fail_count"]

        print(
            f"⚙️ [log_execution] For '{task_name}', using thresholds:\n"
            f"    Efficiency threshold: {eff_thresh}\n"
            f"    Catastrophic threshold: {cat_thresh}\n"
            f"    Ratio window: {ratio_window}\n"
            f"    Ratio fail count: {ratio_fail_count}\n"
        )

        past_attempts = self.get_past_attempts(task_name)

        log_entry = {
            "timestamp": timestamp,
            "execution_trace_id": execution_trace_id,
            "blueprint_id": blueprint_id,
            "blueprint_version": blueprint_version,
            "execution_context": execution_context,
            "task_name": task_name,
            "expected_outcome": expected_outcome,
            "execution_time": float(execution_time),
            "files_changed": files_changed or [],
            "dependencies_affected": dependencies or [],
            "pipeline_connections": pipeline_connections or [],
            "errors_encountered": errors or "None",
            "success": success,
            "efficiency_score": int(efficiency_score),
            "potential_breakage_risk": "High" if not success else "Low",
            "cross_check_required": "Yes" if (not success or dependencies) else "No",
            "previous_attempts": [at["execution_trace_id"] for at in past_attempts],
            "improvement_suggestions": improvement_suggestions or "None"
        }

        # Insert into Chroma: The entire log as "document" plus key metadata
        self.execution_logs.add(
            ids=[execution_trace_id],
            documents=[json.dumps(log_entry)],
            metadatas=[{
                "task_name": task_name,
                "blueprint_id": blueprint_id,
                "timestamp": timestamp,
                "success": success,
                "errors_encountered": errors or "None",
                "efficiency_score": int(efficiency_score)
            }]
        )

        print(f"✅ Execution log stored: {execution_trace_id}")

        # ------------- AUTOMATED BLUEPRINT REVISION PROPOSAL LOGIC -------------
        meltdown_phrases = ["catastrophic meltdown", "catastrophic error", "catastrophic failure"]
        is_catastrophic = False

        if efficiency_score < cat_thresh:
            is_catastrophic = True
        else:
            if errors:
                check_lower = errors.lower()
                for phrase in meltdown_phrases:
                    if phrase in check_lower:
                        is_catastrophic = True
                        break

        # Ratio-based approach
        recent_runs = past_attempts[-(ratio_window - 1):] if ratio_window > 1 else []
        run_data = []
        for attempt in recent_runs:
            run_data.append({
                "success": attempt["success"],
                "efficiency_score": attempt["efficiency_score"]
            })
        run_data.append({
            "success": success,
            "efficiency_score": efficiency_score
        })

        bad_count = 0
        sum_eff = 0
        for rd in run_data:
            sum_eff += rd["efficiency_score"]
            if (not rd["success"]) or (rd["efficiency_score"] < eff_thresh):
                bad_count += 1

        avg_efficiency = sum_eff / len(run_data) if run_data else 100
        repeated_failures = (bad_count >= ratio_fail_count) or (avg_efficiency < eff_thresh)

        reason_string = ""
        revision_triggered = False

        if is_catastrophic:
            revision_triggered = True
            reason_string += (f"[Catastrophic fail] eff={efficiency_score} < {cat_thresh} "
                              f"or meltdown phrase in errors={errors}. ")
        elif repeated_failures:
            revision_triggered = True
            reason_string += (f"[Ratio check] Among last {len(run_data)} runs, {bad_count} were bad "
                              f"(eff < {eff_thresh} or success=False). avg_eff={avg_efficiency:.1f}.")

        if revision_triggered:
            if self.agent_manager:
                print("⚙️ [LLM] Generating improvement notes via LLM... please wait.")
                llm_notes = self.build_llm_improvement_notes(
                    blueprint_id=blueprint_id,
                    logs=run_data,
                    reason=reason_string
                )
                improvement_notes = f"{reason_string}\n\n(LLM-based) {llm_notes}"
            else:
                improvement_notes = f"(Auto) {reason_string}"

            print(f"⚠️  [Revision Trigger] {reason_string}")
            self.generate_blueprint_revision(blueprint_id, improvement_notes)

        return execution_trace_id

    def build_llm_improvement_notes(self, blueprint_id, logs, reason) -> str:
        """Calls the LLM (via self.agent_manager) to produce improvement notes."""
        logs_summary = ""
        for idx, run in enumerate(logs):
            logs_summary += (f"\n• Run #{idx+1}: success={run['success']}, eff={run['efficiency_score']}")

        prompt_text = (
            "You are an AI blueprint improver. You review AI system logs and propose short, direct improvements.\n"
            "No disclaimers, no repeated statements.\n\n"
            f"Blueprint ID: {blueprint_id}\n"
            f"Reason for Proposed Revision:\n{reason}\n"
            f"Relevant Recent Logs:\n{logs_summary}\n\n"
            "Please list bullet-pointed improvements or next steps."
        )

        if not self.agent_manager:
            return f"(LLM not available) {reason}"

        try:
            llm_response = self.agent_manager.send_task("architect", prompt_text, timeout=60)
            if not llm_response or not llm_response.strip():
                return f"(LLM returned nothing) {reason}"
            return llm_response.strip()
        except Exception as e:
            return f"(LLM error: {e}) {reason}"

    def get_thresholds_for_task(self, task_name: str) -> dict:
        """Pull out thresholds for this task from self.thresholds_map, or use defaults."""
        if task_name in self.thresholds_map:
            custom = self.thresholds_map[task_name]
            return {
                "efficiency_threshold": custom.get("efficiency_threshold", self.DEFAULT_EFFICIENCY_THRESHOLD),
                "catastrophic_threshold": custom.get("catastrophic_threshold", self.DEFAULT_CATASTROPHIC_THRESHOLD),
                "ratio_window": custom.get("ratio_window", self.DEFAULT_RATIO_WINDOW),
                "ratio_fail_count": custom.get("ratio_fail_count", self.DEFAULT_RATIO_FAIL_COUNT)
            }
        else:
            return {
                "efficiency_threshold": self.DEFAULT_EFFICIENCY_THRESHOLD,
                "catastrophic_threshold": self.DEFAULT_CATASTROPHIC_THRESHOLD,
                "ratio_window": self.DEFAULT_RATIO_WINDOW,
                "ratio_fail_count": self.DEFAULT_RATIO_FAIL_COUNT
            }

    def get_latest_blueprint_version(self, blueprint_id: str) -> str:
        """Retrieves the latest version of a given blueprint or 'v1.0' if none found."""
        results = self.blueprint_versions.get(where={"blueprint_id": blueprint_id}, limit=1)
        if results and "documents" in results and results["documents"]:
            latest_version_doc = json.loads(results["documents"][0])
            return latest_version_doc.get("blueprint_version", "v1.0")
        return "v1.0"

    def get_past_attempts(self, task_name: str, limit=10) -> list:
        """Retrieves past logs for a given task from the execution_logs collection."""
        print(f"\n🔍 Debugging get_past_attempts() for task: {task_name}")

        results = self.execution_logs.get(where={"task_name": task_name}, limit=limit)
        if not results or "documents" not in results or not results["documents"]:
            print("⚠ No execution logs retrieved by metadata filter.")
            return []

        past_attempts = []
        for doc in results["documents"]:
            log_data = json.loads(doc)
            stored_task_name = log_data.get("task_name", "UNKNOWN")
            short_str = (
                f"  → Found attempt '{log_data.get('execution_trace_id','NOID')}' "
                f"success={log_data.get('success')} eff={log_data.get('efficiency_score')}"
            )
            print(short_str)
            if stored_task_name.strip().lower() == task_name.strip().lower():
                past_attempts.append(log_data)

        print(f"✅ Found {len(past_attempts)} matching past execution attempts.")
        return past_attempts

    def generate_blueprint_revision(self, blueprint_id: str, improvement_notes: str) -> str:
        """Creates a Blueprint Revision Proposal (BRP) in the revision_proposals collection."""
        revision_id = f"brp_{blueprint_id}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        revision_entry = {
            "revision_id": revision_id,
            "timestamp": timestamp,
            "blueprint_id": blueprint_id,
            "improvement_notes": improvement_notes,
            "status": "Pending Review"
        }

        self.revision_proposals.add(
            ids=[revision_id],
            documents=[json.dumps(revision_entry)],
            metadatas=[{"blueprint_id": blueprint_id}]
        )
        print(f"🔹 Blueprint Revision Proposal Generated: {revision_id}")
        return revision_id

# -----------------------------------------------------------
# Example usage to test this script manually (not required)
# -----------------------------------------------------------
if __name__ == "__main__":
    agent_mgr = AgentManager()
    blueprint_exec = BlueprintExecution(agent_manager=agent_mgr, test_mode=False)
    ...
