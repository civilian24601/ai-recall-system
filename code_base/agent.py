#!/usr/bin/env python3
"""
agent.py

Single-agent workflow for the AI Recall System build engine with automated reset, context filtering, simplified prompts, and RAG for ai_coding_guidelines.md.
- Queries aggregator_search for context, filtering out markdown and prioritizing ai_coding_guidelines.md for rules, then Python code.
- Delegates execution to blueprint_execution.
- Manages debug log loop with capped retries, two-LLM processing, and state reset.
- Stages fixes on temporary files, validating before overwriting originals.
"""

import os
import sys
import time
import json
import logging
import chromadb
import subprocess
import re
import shutil
import traceback
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from datetime import datetime

sys.path.append("/mnt/f/projects/ai-recall-system")

from code_base.agent_manager import AgentManager
from scripts.aggregator_search import aggregator_search
from scripts.index_codebase import reindex_single_file
from scripts.blueprint_execution import BlueprintExecution

# Configure basic logging without correlation_id until it's set
logger = logging.getLogger('agent')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)
try:
    log_dir = "/mnt/f/projects/ai-recall-system/logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(f"{log_dir}/agent_debug.log", mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    logger.debug("Logging initialized successfully for agent.py")
except Exception as e:
    print(f"⚠️ Failed to initialize file logging for agent.py: {e}")
    logger.warning("Falling back to console-only logging due to file handler error")

class BuildAgent:
    def __init__(self, test_mode=False):
        """Initialize the BuildAgent with test_mode support and correlation ID."""
        self.correlation_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.agent_manager = AgentManager()
        self.test_mode = test_mode
        self.max_attempts = 6
        self.project_dir = "/mnt/f/projects/ai-recall-system"
        self.backup_dir = f"{self.project_dir}/backups"
        self.test_source_dir = f"{self.project_dir}/tests/test_cases"  # Source directory for test scripts
        self.test_scripts_dir = f"{self.project_dir}/code_base/test_scripts"  # Runtime directory for test scripts
        self.debug_log_file = f"{self.project_dir}/logs/DEBUG_LOGS_TEST.JSON"
        self.embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.collections = {
            "execution_logs": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("execution_logs"),
            "blueprint_versions": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("blueprint_versions"),
            "blueprint_revisions": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("blueprint_revisions"),
            "knowledge_base": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("knowledge_base"),
            "work_sessions": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("work_sessions"),
            "blueprints": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("blueprints"),
            "debugging_logs": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("debugging_logs"),
            "project_codebase": chromadb.PersistentClient(path=f"{self.project_dir}/chroma_db").get_or_create_collection("project_codebase")
        }
        self.blueprint_executor = BlueprintExecution(agent_manager=self.agent_manager, test_mode=self.test_mode, collections=self.collections)
        self.debug_logs = []
        self.load_debug_logs()

        # Reconfigure logging with correlation_id now that it's available
        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - correlation_id:%(correlation_id)s - %(message)s'))
        logger.debug("Logging reconfigured with correlation_id", extra={'correlation_id': self.correlation_id})

        os.makedirs(self.backup_dir, exist_ok=True)

        # Debug: Verify agent_manager has delegate_task
        if not hasattr(self.agent_manager, 'delegate_task'):
            logger.error("AgentManager instance missing delegate_task method", extra={'correlation_id': self.correlation_id})
        else:
            logger.debug("AgentManager instance has delegate_task method", extra={'correlation_id': self.correlation_id})

        print(
            f"🔧 [BuildAgent __init__] Initialized with test_mode={self.test_mode}, correlation_id={self.correlation_id}\n"
            f"Project dir: {self.project_dir}\n"
            f"Collections initialized: {list(self.collections.keys())}\n"
            "AI-driven repair and blueprint execution ready."
        )

    def load_debug_logs(self):
        """Load debug logs from the JSON file."""
        try:
            if os.path.exists(self.debug_log_file):
                with open(self.debug_log_file, "r") as f:
                    self.debug_logs = json.load(f)
            else:
                self.debug_logs = []
            logger.debug(f"Loaded debug logs: {self.debug_logs}", extra={'correlation_id': self.correlation_id})
        except Exception as e:
            logger.error(f"Failed to load debug logs: {e}", extra={'correlation_id': self.correlation_id})
            self.debug_logs = []

    def log_entry(self, collection_name, entry_id, data):
        """Log an entry to the specified collection."""
        collection = self.collections[collection_name]
        meta = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "id": entry_id, "correlation_id": self.correlation_id}
        collection.upsert(
            ids=[entry_id],
            documents=[json.dumps(data)],
            metadatas=[meta]
        )
        logger.info(f"Logged entry '{entry_id}' to {collection_name}", extra={'correlation_id': self.correlation_id})

    def retrieve_context(self, query):
        """Retrieve context for the query using aggregator_search."""
        try:
            results = aggregator_search(query, top_n=3, mode="guidelines_code")
            guidelines_context = [r["document"] for r in results if r.get("metadata", {}).get("filename") == "ai_coding_guidelines.md"]
            code_context = [r["document"] for r in results if r.get("metadata", {}).get("filename", "").endswith(".py")]
            context = "\n".join(guidelines_context[:1] + code_context[:2])
            if not context:
                logger.warning(f"No relevant context (guidelines or Python code) found for query: {query}", extra={'correlation_id': self.correlation_id})
                guidelines_results = aggregator_search(query, top_n=1, mode="guidelines_code")
                guidelines_context = [r["document"] for r in guidelines_results if r.get("metadata", {}).get("filename") == "ai_coding_guidelines.md"]
                context = "\n".join(guidelines_context[:1])[:1000] if guidelines_context else ""
                if not context:
                    logger.error(f"Failed to retrieve any context for query: {query}", extra={'correlation_id': self.correlation_id})
            context = context[:1000] if len(context) > 1000 else context
            logger.debug(f"Filtered context for query '{query}' (guidelines + Python, max 1000 chars): {context}...", extra={'correlation_id': self.correlation_id})
            return context
        except Exception as e:
            logger.error(f"Error retrieving context for query '{query}': {e}", extra={'correlation_id': self.correlation_id})
            return ""

    def reset_state(self):
        """Reset test scripts and debug logs to their initial states using test suite."""
        test_config_path = os.path.join(self.project_dir, "tests", "test_config.json")
        if os.path.exists(test_config_path):
            with open(test_config_path, "r") as f:
                test_config = json.load(f)
            test_ids = test_config.get("test_ids", [])
            expected_results_path = os.path.join(self.project_dir, "tests", "expected_results.json")
            if not os.path.exists(expected_results_path):
                logger.error(f"Expected results file not found: {expected_results_path}", extra={'correlation_id': self.correlation_id})
                return
            with open(expected_results_path, "r") as f:
                expected_results = json.load(f)
            test_scripts = {}
            debug_logs = []
            for test_id in test_ids:
                if test_id not in expected_results:
                    logger.warning(f"Test ID {test_id} not found in expected_results.json", extra={'correlation_id': self.correlation_id})
                    continue
                test_data = expected_results[test_id]
                script_path = os.path.join(self.test_source_dir, test_data["script"].split("/")[-1])
                if not os.path.exists(script_path):
                    logger.warning(f"Test script {script_path} not found for test ID {test_id}", extra={'correlation_id': self.correlation_id})
                    continue
                with open(script_path, "r") as f:
                    script_content = f.read()
                script_name = test_data["script"].split("/")[-1]
                test_scripts[script_name] = script_content
                debug_logs.append({
                    "id": test_id,
                    "error": test_data["error"],
                    "stack_trace": test_data["stack_trace"],
                    "resolved": False
                })
        else:
            logger.error("Test config not found, unable to proceed with reset", extra={'correlation_id': self.correlation_id})
            return  # No fallback to hardcoded tests

        for script_name, content in test_scripts.items():
            backup_path = os.path.join(self.backup_dir, script_name)
            if not os.path.exists(backup_path):
                with open(backup_path, "w") as f:
                    f.write(content.strip() + "\n")

        # Create the runtime test scripts directory if it doesn't exist
        os.makedirs(self.test_scripts_dir, exist_ok=True)

        # Copy scripts from tests/test_cases to code_base/test_scripts
        for script_name, content in test_scripts.items():
            script_path = os.path.join(self.test_scripts_dir, script_name)
            with open(script_path, "w") as f:
                f.write(content.strip() + "\n")

        with open(self.debug_log_file, "w") as f:
            json.dump(debug_logs, f, indent=4)
        logger.debug(f"Reset debug logs to: {json.dumps(debug_logs, indent=4)}", extra={'correlation_id': self.correlation_id})
        logger.info("Reset test scripts and debug logs to initial states.", extra={'correlation_id': self.correlation_id})

    def run(self):
        """Run the agent to process unresolved issues with retry logic."""
        logger.info("Starting Build Agent with blueprint-driven execution and RAG for ai_coding_guidelines.md...", extra={'correlation_id': self.correlation_id})
        
        self.reset_state()
        
        blueprint_path = f"{self.project_dir}/blueprints/agent_blueprint_v1.json"
        if not os.path.exists(blueprint_path):
            logger.error(f"Blueprint not found: {blueprint_path}", extra={'correlation_id': self.correlation_id})
            return

        with open(blueprint_path, "r") as f:
            blueprint = json.load(f)

        attempt_count = 0
        while attempt_count < self.max_attempts:
            with open(self.debug_log_file, "r") as f:
                logs = json.load(f)
            unresolved = [log for log in logs if not log.get("resolved", False)]
            
            if not unresolved:
                logger.info("No unresolved issues—exiting.", extra={'correlation_id': self.correlation_id})
                break
            
            for log in unresolved:
                error_id = log.get("id", f"error_{time.time()}")
                error = log.get("error", "Unknown error")
                stack_trace = log.get("stack_trace", "")
                attempt_count += 1

                script_name = stack_trace.split("'")[1] if "'" in stack_trace else None
                if not script_name:
                    logger.warning(f"Skipping log {error_id}—no script", extra={'correlation_id': self.correlation_id})
                    continue

                # Read from the runtime test scripts directory
                script_path = os.path.join(self.test_scripts_dir, script_name)
                if not os.path.exists(script_path):
                    logger.warning(f"Script {script_name} not found—skipping", extra={'correlation_id': self.correlation_id})
                    continue

                with open(script_path, "r") as f:
                    script_content = f.read()

                context = self.retrieve_context(f"{error} in {script_name}")
                logger.info(f"Filtered context for {error_id} (guidelines + Python, max 1000 chars): {context}...", extra={'correlation_id': self.correlation_id})

                task_prompt = (
                    f"Please debug the following script and return ONLY the COMPLETE fixed function in Python using a FULL try/except block "
                    f"with the appropriate except clause to handle the error ({error}), returning None, with NO extra logic, NO prose, "
                    f"and NO explanations, inside ```python\n{script_content}\n```."
                )
                fix = self.agent_manager.delegate_task("engineer", task_prompt, timeout=300, correlation_id=self.correlation_id)
                logger.debug(f"Debug: Engineer's fix for {error_id}: {fix}", extra={'correlation_id': self.correlation_id})

                if fix is None or not fix.strip():
                    if attempt_count < self.max_attempts:
                        logger.warning(f"No valid fix for {error_id} after {attempt_count} attempts. Retrying...", extra={'correlation_id': self.correlation_id})
                        fix = self.agent_manager.delegate_task(
                            "engineer",
                            f"Please debug the following script and return ONLY the COMPLETE fixed function in Python using a FULL try/except block "
                            f"with the appropriate except clause to handle the error ({error}), returning None, with NO extra logic, NO prose, "
                            f"and NO explanations, inside ```python\n{script_content}\n```.",
                            timeout=360,
                            correlation_id=self.correlation_id
                        )
                    else:
                        logger.error(f"Max attempts reached for {error_id}—skipping fix to preserve script.", extra={'correlation_id': self.correlation_id})
                        fix = None
                elif not isinstance(fix, str) or not fix.strip():
                    logger.warning(f"Invalid fix format for {error_id}—skipping fix.", extra={'correlation_id': self.correlation_id})
                    fix = None
                
                if fix and "```python" in fix:
                    try:
                        fix = re.search(r"```python\s*(.*?)\s*```", fix, re.DOTALL).group(1).strip()
                    except AttributeError:
                        logger.warning(f"Fix for {error_id} not in expected ```python``` format—using raw response.", extra={'correlation_id': self.correlation_id})
                        fix = fix if isinstance(fix, str) else None
                else:
                    fix = fix if isinstance(fix, str) and fix.strip() else None

                reviewed_fix = None
                if fix is not None:
                    review_prompt = (
                        f"Please review this response: {fix if fix.strip() else 'def placeholder(): pass'}. Strip all prose, test cases, <think> blocks, and irrelevant code. "
                        f"Return ONLY the COMPLETE fixed function in Python using a FULL try/except block with the appropriate except clause "
                        f"to handle the error ({error}), returning None, with NO extra logic, NO prose, and NO explanations, inside ```python ... ```."
                    )
                    reviewed_fix = self.agent_manager.delegate_task("reviewer", review_prompt, timeout=300, correlation_id=self.correlation_id)
                    logger.debug(f"Debug: Reviewed fix for {error_id}: {reviewed_fix}", extra={'correlation_id': self.correlation_id})

                final_fix = fix if fix and fix.strip() else None
                if reviewed_fix and isinstance(reviewed_fix, str) and reviewed_fix.strip():
                    if "```python" in reviewed_fix:
                        try:
                            reviewed_fix = re.search(r"```python\s*(.*?)\s*```", reviewed_fix, re.DOTALL).group(1).strip()
                            final_fix = reviewed_fix
                        except AttributeError:
                            logger.warning(f"Reviewed fix for {error_id} not in expected ```python``` format—using original fix.", extra={'correlation_id': self.correlation_id})
                    else:
                        final_fix = reviewed_fix

                logger.debug(f"Debug: Final fix for {error_id}: {final_fix}", extra={'correlation_id': self.correlation_id})

                temp_script_path = script_path + ".tmp"
                if os.path.exists(temp_script_path):
                    os.remove(temp_script_path)
                    logger.debug(f"Cleaned up existing temp file: {temp_script_path}", extra={'correlation_id': self.correlation_id})

                fix_works = False
                fix_error = "No validation performed"
                if final_fix:
                    temp_script_path = script_path + ".tmp"
                    shutil.copy(script_path, temp_script_path)
                    with open(temp_script_path, "r") as f:
                        original_content = f.read()
                    with open(temp_script_path, "w") as f:
                        func_match = re.search(r"def\s+\w+\s*\(.*?\):.*?(?=\n\n|\Z)", original_content, re.DOTALL)
                        if func_match:
                            f.write(original_content.replace(func_match.group(0), final_fix) + "\n")
                        else:
                            f.write(final_fix + "\n" + original_content)

                    # Pass the test_input from the log entry
                    test_input = log.get("test_input", None)
                    fix_works, fix_error = self.agent_manager.test_fix(temp_script_path, error, stack_trace, final_fix, test_input_str=test_input)
                    logger.debug(f"Validation result for {error_id}: fix_works={fix_works}, fix_error={fix_error}", extra={'correlation_id': self.correlation_id})

                logger.debug(f"Calling run_blueprint for {error_id} with original_error: {error}, script_path: {script_path}", extra={'correlation_id': self.correlation_id})

                blueprint_id = f"bp_fix_{error_id}"
                execution_trace_id, validation_result = self.blueprint_executor.run_blueprint(
                    blueprint_id=blueprint_id,
                    task_name="Apply fix",
                    script_path=script_path,
                    execution_context=context,
                    final_fix=final_fix,
                    original_error=error if error else "Unknown error",
                    stack_trace=stack_trace,
                    correlation_id=self.correlation_id
                )
                
                if execution_trace_id:
                    fix_works = validation_result.get("fix_works", False)
                    fix_error = validation_result.get("fix_error", "No validation performed")
                    log_result = self.collections["execution_logs"].get(ids=[execution_trace_id])
                    log_data = json.loads(log_result["documents"][0]) if log_result["documents"] else {}
                    success = log_data.get("success", False)
                    
                    resolved = fix_works
                    
                    log_entry = {
                        "id": error_id,
                        "error": error,
                        "stack_trace": stack_trace,
                        "fix": final_fix,
                        "codestral_fix": fix,
                        "reviewed_fix": reviewed_fix if reviewed_fix else "None",
                        "resolved": resolved,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "execution_trace_id": execution_trace_id,
                        "test_result": "Success" if fix_works else f"Failed: {fix_error}",
                        "attempts": attempt_count,
                        "test_input": str(validation_result.get("test_input", "N/A")),
                        "expected_result": str(validation_result.get("expected_result", "N/A")),
                        "correlation_id": self.correlation_id
                    }
                    self.log_entry("debugging_logs", error_id, log_entry)
                    
                    reindex_single_file(script_path, self.collections["project_codebase"], self.embed_model)
                    logger.info(f"Reindexed {script_path}", extra={'correlation_id': self.correlation_id})
                    
                    logs = [l if l["id"] != error_id else log_entry for l in logs]
                    with open(self.debug_log_file, "w") as f:
                        json.dump(logs, f, indent=4)
                    logger.debug(f"Updated debug logs for {error_id}: {json.dumps(log_entry, indent=4)}", extra={'correlation_id': self.correlation_id})

            if attempt_count >= self.max_attempts:
                logger.error("Max attempts reached for unresolved issues—exiting.", extra={'correlation_id': self.correlation_id})
                break

        logger.info("Completed run and reset state for next test.", extra={'correlation_id': self.correlation_id})
        self.reset_state()

if __name__ == "__main__":
    agent = BuildAgent(test_mode=True)
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n⏹️ Execution interrupted by user.")
        agent.reset_state()
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}, traceback: {traceback.format_exc()}", extra={'correlation_id': agent.correlation_id})
        agent.reset_state()