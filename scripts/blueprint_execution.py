#!/usr/bin/env python3
"""
Blueprint Execution Script with LLM-Generated Improvement Notes

File path: /mnt/f/projects/ai-recall-system/scripts/blueprint_execution.py
"""

# Blueprint Version
BLUEPRINT_VERSION = "v2.1"

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

# Configure logging (moved inside __init__ to handle correlation_id)
logger = logging.getLogger('blueprint_execution')

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

        # Configure logging here to ensure correlation_id is available
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - correlation_id:%(correlation_id)s - %(message)s'))
        logger.addHandler(console_handler)
        try:
            log_dir = "/mnt/f/projects/ai-recall-system/logs"
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(f"{log_dir}/blueprint_debug.log", mode='a')
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - correlation_id:%(correlation_id)s - %(message)s'))
            logger.addHandler(file_handler)
            logger.debug("Logging initialized successfully for blueprint_execution.py", extra={'correlation_id': self.correlation_id or 'N/A'})
        except Exception as e:
            print(f"⚠️ Failed to initialize file logging for blueprint_execution.py: {e}")
            logger.warning("Falling back to console-only logging due to file handler error", extra={'correlation_id': self.correlation_id or 'N/A'})

        print(
            f"⚙️ [BlueprintExecution __init__] Default thresholds:\n"
            f"    Efficiency threshold: {self.DEFAULT_EFFICIENCY_THRESHOLD}\n"
            f"    Catastrophic threshold: {self.DEFAULT_CATASTROPHIC_THRESHOLD}\n"
            f"    Ratio window: {self.DEFAULT_RATIO_WINDOW}\n"
            f"    Ratio fail count: {self.DEFAULT_RATIO_FAIL_COUNT}\n"
            f"test_mode={test_mode}, using {'test' if test_mode else 'production'} collections\n"
            "LLM-based improvement notes enabled with agent_manager."
        )

    def run_blueprint(self, blueprint_id, task_name, script_path, execution_context, final_fix=None, original_error=None, stack_trace=None, correlation_id=None):
        """Executes a blueprint task, logs BELog, evolves if improved."""
        print(f"⚙️ Running blueprint {blueprint_id}: {task_name}")
        
        logger.debug(f"Entering run_blueprint with blueprint_id: {blueprint_id}, task_name: {task_name}, script_path: {script_path}, "
                     f"final_fix: {final_fix}, original_error: {original_error}, stack_trace: {stack_trace}", extra={'correlation_id': correlation_id or 'N/A'})

        start_time = time.time()
        temp_script_path = script_path + ".tmp"
        try:
            logger.debug(f"Starting blueprint execution for task '{task_name}' with script_path: {script_path}, original_error: {original_error}", extra={'correlation_id': correlation_id or 'N/A'})

            if task_name == "Apply fix":
                if not final_fix:
                    logger.error("final_fix is required for 'Apply fix' task", extra={'correlation_id': correlation_id or 'N/A'})
                    raise ValueError("final_fix is required for 'Apply fix' task")
                
                logger.debug(f"Copying script {script_path} to temp file {temp_script_path}", extra={'correlation_id': correlation_id or 'N/A'})
                shutil.copy(script_path, temp_script_path)
                with open(temp_script_path, "r") as f:
                    original_content = f.read()
                logger.debug(f"Original content of {temp_script_path}: {original_content}", extra={'correlation_id': correlation_id or 'N/A'})
                with open(temp_script_path, "w") as f:
                    f.write(final_fix + "\n")
                logger.debug(f"Updated content of {temp_script_path} with fix: {final_fix}", extra={'correlation_id': correlation_id or 'N/A'})

                logger.debug(f"Validating fix for {script_path} with original_error: {original_error}", extra={'correlation_id': correlation_id or 'N/A'})
                fix_works = False
                fix_error = "No validation performed"
                try:
                    fix_works, fix_error = self.agent_manager.test_fix(temp_script_path, original_error, stack_trace, final_fix)
                    logger.debug(f"Validation result for {script_path}: fix_works={fix_works}, fix_error={fix_error}", extra={'correlation_id': correlation_id or 'N/A'})
                except Exception as e:
                    logger.error(f"Validation failed for {script_path}: {e}, traceback: {traceback.format_exc()}", extra={'correlation_id': correlation_id or 'N/A'})
                    fix_error = str(e)
                finally:
                    logger.debug(f"Final validation result: fix_works={fix_works}, fix_error={fix_error}", extra={'correlation_id': correlation_id or 'N/A'})
                
                if fix_works:
                    logger.debug(f"Validation passed, applying fix by moving {temp_script_path} to {script_path}", extra={'correlation_id': correlation_id or 'N/A'})
                    shutil.move(temp_script_path, script_path)
                    logger.info(f"Applied valid fix to {script_path}", extra={'correlation_id': correlation_id or 'N/A'})
                    task_result = final_fix
                    success = True
                else:
                    if os.path.exists(temp_script_path):
                        os.remove(temp_script_path)
                        logger.debug(f"Cleaned up temp file after validation failure: {temp_script_path}", extra={'correlation_id': correlation_id or 'N/A'})
                    logger.warning(f"Fix for {task_name} failed validation: {fix_error}—preserving original script.", extra={'correlation_id': correlation_id or 'N/A'})
                    task_result = None
                    success = False
            else:
                logger.debug(f"Task '{task_name}' is not 'Apply fix', delegating to engineer", extra={'correlation_id': correlation_id or 'N/A'})
                task_result = self.agent_manager.delegate_task(
                    "engineer",
                    f"Execute task '{task_name}' on script {script_path} with context: {execution_context}",
                    timeout=300,
                    correlation_id=correlation_id
                )
                success = task_result and "def placeholder" not in task_result

            execution_time = time.time() - start_time
            errors = "None" if task_result and "def placeholder" not in task_result else "Task execution failed" if not success else "None"
            efficiency_score = int(100 - (execution_time * 10)) if success else 20
            
            logger.debug(f"Logging execution result: success={success}, errors={errors}, efficiency_score={efficiency_score}", extra={'correlation_id': correlation_id or 'N/A'})
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
                improvement_suggestions="None" if success else "Adjust execution logic",
                correlation_id=correlation_id
            )
            
            self.evolve_blueprint(blueprint_id, execution_trace_id, success)
            logger.debug(f"Completed run_blueprint for {blueprint_id}, returning execution_trace_id: {execution_trace_id}", extra={'correlation_id': correlation_id or 'N/A'})
            return execution_trace_id, {
                "fix_works": fix_works,
                "fix_error": fix_error if not fix_works else "",
                "test_input": getattr(self.agent_manager, 'test_input', 'N/A'),
                "expected_result": getattr(self.agent_manager, 'expected_result', 'N/A')
            }
        except Exception as e:
            print(f"⚠️ Blueprint execution failed: {e}")
            logger.error(f"Exception in run_blueprint: {e}, traceback: {traceback.format_exc()}", extra={'correlation_id': correlation_id or 'N/A'})
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
                logger.debug(f"Cleaned up temp file after failure: {temp_script_path}", extra={'correlation_id': correlation_id or 'N/A'})
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
                improvement_suggestions="Debug execution failure",
                correlation_id=correlation_id
            ), {"fix_works": False, "fix_error": str(e)}

    def log_execution(self, blueprint_id, task_name, execution_context, expected_outcome, execution_time, files_changed, dependencies, pipeline_connections, errors, success, efficiency_score, improvement_suggestions, correlation_id=None):
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
            "improvement_suggestions": improvement_suggestions or "None",
            "correlation_id": correlation_id or 'N/A'
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
                "efficiency_score": int(efficiency_score),
                "correlation_id": correlation_id or 'N/A'
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
        correlation_id = log_data.get("correlation_id", 'N/A')
        
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
                "last_execution": execution_trace_id,
                "correlation_id": correlation_id
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