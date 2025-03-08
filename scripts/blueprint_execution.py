#!/usr/bin/env python3
"""
Blueprint Execution Script with LLM-Generated Improvement Notes

File path: /mnt/f/projects/ai-recall-system/scripts/blueprint_execution.py
"""

import sys
import os
import datetime
import json
import traceback
import time
import chromadb
import logging
import shutil
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(PARENT_DIR)

from code_base.agent_manager import AgentManager

# Configure logging
try:
    log_dir = "/mnt/f/projects/ai-recall-system/logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"{log_dir}/blueprint_debug.log", mode='a')  # Changed to 'a' for append
        ]
    )
    logging.debug("Logging initialized successfully for blueprint_execution.py")
    # Verify file handler is working
    with open(f"{log_dir}/blueprint_debug.log", "a") as f:
        f.write("Test write to verify file handler\n")
except Exception as e:
    print(f"⚠️ Failed to initialize logging for blueprint_execution.py: {e}")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.warning("Falling back to console-only logging due to file handler error")

class BlueprintExecution:
    def __init__(self, agent_manager=None, test_mode=False, collections=None):
        self.agent_manager = agent_manager or AgentManager()
        self.test_mode = test_mode
        self.collections = collections
        
        if not self.collections:
            raise ValueError("Collections must be provided to BlueprintExecution")
        
        self.thresholds_map = {}
        self.DEFAULT_EFFICIENCY_THRESHOLD = 70
        self.DEFAULT_CATASTROPHIC_THRESHOLD = 30
        self.DEFAULT_RATIO_WINDOW = 3
        self.DEFAULT_RATIO_FAIL_COUNT = 2

        print(
            f"⚙️ [BlueprintExecution __init__] Default thresholds:\n"
            f"    Efficiency threshold: {self.DEFAULT_EFFICIENCY_THRESHOLD}\n"
            f"    Catastrophic threshold: {self.DEFAULT_CATASTROPHIC_THRESHOLD}\n"
            f"    Ratio window: {self.DEFAULT_RATIO_WINDOW}\n"
            f"    Ratio fail count: {self.DEFAULT_RATIO_FAIL_COUNT}\n"
            f"test_mode={test_mode}, using {'test' if test_mode else 'production'} collections\n"
            "LLM-based improvement notes enabled with agent_manager."
        )

    def run_blueprint(self, blueprint_id, task_name, script_path, execution_context, final_fix=None, original_error=None):
        """Executes a blueprint task, logs BELog, evolves if improved."""
        print(f"⚙️ Running blueprint {blueprint_id}: {task_name}")
        
        logging.debug(f"Entering run_blueprint with blueprint_id: {blueprint_id}, task_name: {task_name}, script_path: {script_path}, "
                     f"final_fix: {final_fix}, original_error: {original_error}")

        start_time = time.time()
        temp_script_path = script_path + ".tmp"
        try:
            logging.debug(f"Starting blueprint execution for task '{task_name}' with script_path: {script_path}, original_error: {original_error}")

            if task_name == "Apply fix":
                if not final_fix:
                    logging.error("final_fix is required for 'Apply fix' task")
                    raise ValueError("final_fix is required for 'Apply fix' task")
                
                logging.debug(f"Copying script {script_path} to temp file {temp_script_path}")
                shutil.copy(script_path, temp_script_path)
                with open(temp_script_path, "r") as f:
                    original_content = f.read()
                logging.debug(f"Original content of {temp_script_path}: {original_content}")
                with open(temp_script_path, "w") as f:
                    func_match = re.search(r"def\s+\w+\s*$$ .*? $$:.*?(?=\n\n|\Z)", original_content, re.DOTALL)
                    if func_match:
                        f.write(original_content.replace(func_match.group(0), final_fix) + "\n")
                    else:
                        f.write(final_fix + "\n" + original_content)
                logging.debug(f"Updated content of {temp_script_path} with fix: {final_fix}")

                logging.debug(f"Validating fix for {script_path} with original_error: {original_error}")
                fix_works = False
                fix_error = "No validation performed"
                try:
                    fix_works, fix_error = self.agent_manager.test_fix(temp_script_path, original_error)
                    logging.debug(f"Validation result for {script_path}: fix_works={fix_works}, fix_error={fix_error}")
                except Exception as e:
                    logging.error(f"Validation failed for {script_path}: {e}, traceback: {traceback.format_exc()}")
                    fix_error = str(e)
                finally:
                    logging.debug(f"Final validation result: fix_works={fix_works}, fix_error={fix_error}")
                
                if fix_works:
                    logging.debug(f"Validation passed, applying fix by moving {temp_script_path} to {script_path}")
                    shutil.move(temp_script_path, script_path)
                    logging.info(f"Applied valid fix to {script_path}")
                    task_result = final_fix
                    success = True
                else:
                    if os.path.exists(temp_script_path):
                        os.remove(temp_script_path)
                        logging.debug(f"Cleaned up temp file after validation failure: {temp_script_path}")
                    logging.warning(f"Fix for {task_name} failed validation: {fix_error}—preserving original script.")
                    task_result = None
                    success = False
            else:
                logging.debug(f"Task '{task_name}' is not 'Apply fix', delegating to engineer")
                task_result = self.agent_manager.delegate_task(
                    "engineer",
                    f"Execute task '{task_name}' on script {script_path} with context: {execution_context}",
                    timeout=300
                )
                success = task_result and "def placeholder" not in task_result

            execution_time = time.time() - start_time
            errors = "None" if task_result and "def placeholder" not in task_result else "Task execution failed" if not success else "None"
            efficiency_score = int(100 - (execution_time * 10)) if success else 20
            
            logging.debug(f"Logging execution result: success={success}, errors={errors}, efficiency_score={efficiency_score}")
            execution_trace_id = self.log_execution(
                blueprint_id=blueprint_id,
                task_name=task_name,
                execution_context=execution_context,
                expected_outcome="Task completed successfully",
                execution_time=execution_time,
                files_changed=[script_path],
                dependencies=[],
                pipeline_connections=["agent.py"],
                errors=errors,
                success=success,
                efficiency_score=efficiency_score,
                improvement_suggestions="None" if success else "Adjust execution logic"
            )
            
            self.evolve_blueprint(blueprint_id, execution_trace_id, success)
            logging.debug(f"Completed run_blueprint for {blueprint_id}, returning execution_trace_id: {execution_trace_id}")
            return execution_trace_id, {"fix_works": fix_works, "fix_error": fix_error if not fix_works else ""}
        except Exception as e:
            print(f"⚠️ Blueprint execution failed: {e}")
            logging.error(f"Exception in run_blueprint: {e}, traceback: {traceback.format_exc()}")
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
                logging.debug(f"Cleaned up temp file after failure: {temp_script_path}")
            execution_time = time.time() - start_time
            return self.log_execution(
                blueprint_id=blueprint_id,
                task_name=task_name,
                execution_context=execution_context,
                expected_outcome="Task completed successfully",
                execution_time=execution_time,
                files_changed=[script_path],
                dependencies=[],
                pipeline_connections=["agent.py"],
                errors=str(e),
                success=False,
                efficiency_score=10,
                improvement_suggestions="Debug execution failure"
            ), {"fix_works": False, "fix_error": str(e)}

    def log_execution(self, blueprint_id, task_name, execution_context, expected_outcome, execution_time, files_changed, dependencies, pipeline_connections, errors, success, efficiency_score, improvement_suggestions):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execution_trace_id = f"log_{timestamp.replace(' ', '_')}"
        blueprint_version = self.get_latest_blueprint_version(blueprint_id)
        thresholds = self.get_thresholds_for_task(task_name)

        print(
            f"⚙️ [log_execution] For '{task_name}', thresholds:\n"
            f"    Efficiency: {thresholds['efficiency_threshold']}\n"
            f"    Catastrophic: {thresholds['catastrophic_threshold']}\n"
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

        self.collections["execution_logs"].add(
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
        return execution_trace_id

    def evolve_blueprint(self, blueprint_id, execution_trace_id, success):
        """Evolves blueprint if successful or improved."""
        log_result = self.collections["execution_logs"].get(ids=[execution_trace_id])
        if not log_result["documents"]:
            return
        
        log_data = json.loads(log_result["documents"][0])
        improvement_suggestions = log_data["improvement_suggestions"]
        
        if success or improvement_suggestions != "None":
            current_version = self.get_latest_blueprint_version(blueprint_id)
            version_parts = current_version.split(".")
            new_version = f"v{int(version_parts[0][1:]) + (1 if success else 0)}.{int(version_parts[1]) + (1 if not success else 0)}"
            
            blueprint_data = {
                "blueprint_id": blueprint_id,
                "version": new_version,
                "parent_version": current_version,
                "task_name": log_data["task_name"],
                "execution_context": log_data["execution_context"],
                "improvements": improvement_suggestions,
                "last_execution": execution_trace_id
            }
            self.collections["blueprint_versions"].add(
                ids=[f"{blueprint_id}_{new_version}"],
                documents=[json.dumps(blueprint_data)],
                metadatas=[{"blueprint_id": blueprint_id}]
            )
            print(f"🔹 Blueprint evolved: {blueprint_id}_{new_version}")

    def get_thresholds_for_task(self, task_name):
        return self.thresholds_map.get(task_name, {
            "efficiency_threshold": self.DEFAULT_EFFICIENCY_THRESHOLD,
            "catastrophic_threshold": self.DEFAULT_CATASTROPHIC_THRESHOLD,
            "ratio_window": self.DEFAULT_RATIO_WINDOW,
            "ratio_fail_count": self.DEFAULT_RATIO_FAIL_COUNT
        })

    def get_latest_blueprint_version(self, blueprint_id):
        results = self.collections["blueprint_versions"].get(where={"blueprint_id": blueprint_id}, limit=1)
        return json.loads(results["documents"][0]).get("version", "v1.0") if results["documents"] else "v1.0"

    def get_past_attempts(self, task_name, limit=10):
        results = self.collections["execution_logs"].get(where={"task_name": task_name}, limit=10)
        return [json.loads(doc) for doc in results["documents"]] if results["documents"] else []

    def generate_blueprint_revision(self, blueprint_id, improvement_notes):
        revision_id = f"brp_{blueprint_id}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        revision_entry = {
            "revision_id": revision_id,
            "timestamp": timestamp,
            "blueprint_id": blueprint_id,
            "improvement_notes": improvement_notes,
            "status": "Pending Review"
        }
        
        self.collections["blueprint_revisions"].add(
            ids=[revision_id],
            documents=[json.dumps(revision_entry)],
            metadatas=[{"blueprint_id": blueprint_id}]
        )
        print(f"🔹 Blueprint Revision Proposal Generated: {revision_id}")
        return revision_id

if __name__ == "__main__":
    CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
    collections = {
        "execution_logs": chromadb.PersistentClient(path=CHROMA_DB_PATH).get_or_create_collection("execution_logs"),
        "blueprint_versions": chromadb.PersistentClient(path=CHROMA_DB_PATH).get_or_create_collection("blueprint_versions"),
        "blueprint_revisions": chromadb.PersistentClient(path=CHROMA_DB_PATH).get_or_create_collection("blueprint_revisions")
    }
    executor = BlueprintExecution(collections=collections)
    executor.run_blueprint("bp_001", "Query error handling", "/mnt/f/projects/ai-recall-system/scripts/retrieve_codebase.py", "Enhance AI debugging recall")