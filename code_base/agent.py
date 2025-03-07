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
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

sys.path.append("/mnt/f/projects/ai-recall-system")

from code_base.agent_manager import AgentManager
from scripts.aggregator_search import aggregator_search
from scripts.index_codebase import reindex_single_file
from scripts.blueprint_execution import BlueprintExecution

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BuildAgent:
    def __init__(self, project_dir="/mnt/f/projects/ai-recall-system", test_mode=False):
        self.project_dir = project_dir
        self.test_mode = test_mode
        self.agent_manager = AgentManager()
        self.embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.chroma_client = chromadb.PersistentClient(path=f"{project_dir}/chroma_db")
        self.logs_dir = f"{project_dir}/logs"
        os.makedirs(self.logs_dir, exist_ok=True)
        self.debug_log_file = f"{self.logs_dir}/debug_logs{'_test' if test_mode else ''}.json"
        self.max_attempts = 5
        self.backup_dir = f"{project_dir}/code_base/test_scripts/backup/"
        os.makedirs(self.backup_dir, exist_ok=True)

        self.collections = {
            "knowledge_base": self.chroma_client.get_or_create_collection(
                name="knowledge_base" if not self.test_mode else "knowledge_base_test"
            ),
            "execution_logs": self.chroma_client.get_or_create_collection(
                name="execution_logs" if not self.test_mode else "execution_logs_test"
            ),
            "debugging_logs": self.chroma_client.get_or_create_collection(
                name="debugging_logs" if not self.test_mode else "debugging_logs_test"
            ),
            "project_codebase": self.chroma_client.get_or_create_collection(
                name="project_codebase" if not self.test_mode else "project_codebase_test"
            ),
            "blueprint_versions": self.chroma_client.get_or_create_collection(
                name="blueprint_versions" if not self.test_mode else "blueprint_versions_test"
            ),
            "blueprint_revisions": self.chroma_client.get_or_create_collection(
                name="blueprint_revisions" if not self.test_mode else "blueprint_revisions_test"
            ),
            "markdown_logs": self.chroma_client.get_or_create_collection(
                name="markdown_logs" if not self.test_mode else "markdown_logs_test"
            )
        }
        self.blueprint_executor = BlueprintExecution(
            agent_manager=self.agent_manager,
            test_mode=self.test_mode,
            collections=self.collections
        )

    def log_entry(self, collection_name, entry_id, data):
        collection = self.collections[collection_name]
        meta = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "id": entry_id}
        collection.upsert(
            ids=[entry_id],
            documents=[json.dumps(data)],
            metadatas=[meta]
        )
        logging.info(f"Logged entry '{entry_id}' to {collection_name}")

    def retrieve_context(self, query):
        try:
            results = aggregator_search(query, top_n=3, mode="guidelines_code")
            guidelines_context = [r["document"] for r in results if r.get("metadata", {}).get("filename") == "ai_coding_guidelines.md"]
            code_context = [r["document"] for r in results if r.get("metadata", {}).get("filename", "").endswith(".py")]
            context = "\n".join(guidelines_context[:1] + code_context[:2])
            if not context:
                logging.warning(f"No relevant context (guidelines or Python code) found for query: {query}")
                guidelines_results = aggregator_search(query, top_n=1, mode="guidelines")
                guidelines_context = [r["document"] for r in guidelines_results if r.get("metadata", {}).get("filename") == "ai_coding_guidelines.md"]
                context = "\n".join(guidelines_context[:1])[:1000] if guidelines_context else ""
                if not context:
                    logging.error(f"Failed to retrieve any context for query: {query}")
            context = context[:1000] if len(context) > 1000 else context
            logging.debug(f"Filtered context for query '{query}' (guidelines + Python, max 1000 chars): {context}...")
            return context
        except Exception as e:
            logging.error(f"Error retrieving context for query '{query}': {e}")
            return ""

    def test_fix(self, script_path, original_error):
        """Test if the fix handles the original error."""
        try:
            with open(script_path, "r") as f:
                script_content = f.read()
            func_match = re.search(r"def\s+(\w+)\s*\(", script_content)
            if not func_match:
                return False, "No function definition found"
            func_name = func_match.group(1)

            test_code = f"""
import sys
from io import StringIO
def run_test():
    original_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        if "{func_name}" == "divide":
            result = {func_name}(10, 0)
        elif "{func_name}" == "authenticate_user":
            result = {func_name}({{'password': 'secure123'}})
        sys.stdout = original_stdout
        return result is not None or "Handled" in sys.stdout.getvalue()
    except Exception as e:
        sys.stdout = original_stdout
        return False, str(e)
result, error = run_test()
print("Test result:", "Success" if result else f"Failed: {{error}}")
"""
            temp_test_path = script_path + ".test"
            with open(temp_test_path, "w") as f:
                f.write(script_content + "\n" + test_code)
            result = subprocess.run(
                ["python3", temp_test_path],
                capture_output=True, text=True, timeout=10
            )
            os.remove(temp_test_path)
            output = result.stdout.strip()
            if "Test result: Success" in output or "Handled" in output:
                return True, ""
            return False, result.stderr or "Fix did not handle the original error"
        except subprocess.TimeoutExpired:
            return False, "Timeout: Script hung"
        except Exception as e:
            return False, str(e)

    def reset_state(self):
        test_scripts = {
            "test_script.py": """
def divide(a, b):
    return a / b  # Fails on b=0
""",
            "user_auth.py": """
def authenticate_user(user_data):
    return user_data["username"]  # Fails if 'username' missing
"""
        }
        debug_logs = [
            {"id": "test1", "error": "ZeroDivisionError", "stack_trace": "File 'test_script.py', line 3", "resolved": False},
            {"id": "test2", "error": "KeyError", "stack_trace": "File 'user_auth.py', line 5", "resolved": False}
        ]

        for script_name, content in test_scripts.items():
            backup_path = os.path.join(self.backup_dir, script_name)
            if not os.path.exists(backup_path):
                with open(backup_path, "w") as f:
                    f.write(content.strip() + "\n")
        
        for script_name, content in test_scripts.items():
            script_path = os.path.join(self.project_dir, "code_base/test_scripts", script_name)
            with open(script_path, "w") as f:
                f.write(content.strip() + "\n")

        with open(self.debug_log_file, "w") as f:
            json.dump(debug_logs, f, indent=4)

        logging.info("Reset test scripts and debug logs to initial states.")

    def run(self):
        logging.info("Starting Build Agent with blueprint-driven execution and RAG for ai_coding_guidelines.md...")
        
        self.reset_state()
        
        blueprint_path = f"{self.project_dir}/blueprints/agent_blueprint_v1.json"
        if not os.path.exists(blueprint_path):
            logging.error(f"Blueprint not found: {blueprint_path}")
            return

        with open(blueprint_path, "r") as f:
            blueprint = json.load(f)

        attempt_count = 0
        while attempt_count < self.max_attempts:
            with open(self.debug_log_file, "r") as f:
                logs = json.load(f)
            unresolved = [log for log in logs if not log.get("resolved", False)]
            
            if not unresolved:
                logging.info("No unresolved issues—exiting.")
                break
            
            for log in unresolved:
                error_id = log.get("id", f"error_{time.time()}")
                error = log.get("error", "Unknown error")
                stack_trace = log.get("stack_trace", "")
                attempt_count += 1

                script_name = stack_trace.split("'")[1] if "'" in stack_trace else None
                if not script_name:
                    logging.warning(f"Skipping log {error_id}—no script")
                    continue

                script_path = os.path.join(self.project_dir, "code_base/test_scripts", script_name)
                if not os.path.exists(script_path):
                    logging.warning(f"Script {script_name} not found—skipping")
                    continue

                with open(script_path, "r") as f:
                    script_content = f.read()

                context = self.retrieve_context(f"{error} in {script_name}")
                logging.info(f"Filtered context for {error_id} (guidelines + Python, max 1000 chars): {context}...")

                task_prompt = (
                    f"Please debug the following script and return ONLY the COMPLETE fixed function in Python using a FULL try/except block "
                    f"with the appropriate except clause to handle the error ({error}), returning None, with NO extra logic, NO prose, "
                    f"and NO explanations, inside ```python\n{script_content}\n```."
                )
                fix = self.agent_manager.delegate_task("engineer", task_prompt, timeout=300)
                
                if fix is None or not fix.strip():
                    if attempt_count < self.max_attempts:
                        logging.warning(f"No valid fix for {error_id} after {attempt_count} attempts. Retrying...")
                        fix = self.agent_manager.delegate_task(
                            "engineer",
                            f"Please debug the following script and return ONLY the COMPLETE fixed function in Python using a FULL try/except block "
                            f"with the appropriate except clause to handle the error ({error}), returning None, with NO extra logic, NO prose, "
                            f"and NO explanations, inside ```python\n{script_content}\n```.",
                            timeout=360
                        )
                    else:
                        logging.error(f"Max attempts reached for {error_id}—skipping fix to preserve script.")
                        fix = None
                elif not isinstance(fix, str) or not fix.strip():
                    logging.warning(f"Invalid fix format for {error_id}—skipping fix.")
                    fix = None
                
                if fix and "```python" in fix:
                    try:
                        fix = re.search(r"```python\s*(.*?)\s*```", fix, re.DOTALL).group(1).strip()
                    except AttributeError:
                        logging.warning(f"Fix for {error_id} not in expected ```python``` format—skipping fix.")
                        fix = None
                else:
                    raw_func = re.search(r"def\s+(\w+)\s*$$ .*? $$:.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None)", fix, re.DOTALL | re.MULTILINE)
                    if raw_func:
                        fix = raw_func.group(0).strip()
                    else:
                        logging.warning(f"Fix for {error_id} not a string or missing valid ```python``` or specific try/except—skipping fix.")
                        fix = None

                # Ensure reviewer processes the correct fix
                reviewed_fix = None
                if fix:
                    review_prompt = (
                        f"Please review this response: {fix}. Strip all prose, test cases, <think> blocks, and irrelevant code. "
                        f"Return ONLY the COMPLETE fixed function in Python using a FULL try/except block with the appropriate except clause "
                        f"to handle the error ({error}), returning None, with NO extra logic, NO prose, and NO explanations, inside ```python ... ```."
                    )
                    reviewed_fix = self.agent_manager.delegate_task("reviewer", review_prompt, timeout=300)
                    logging.debug(f"Debug: Reviewed fix for {error_id}: {reviewed_fix}")

                final_fix = fix  # Default to engineer's fix
                if reviewed_fix and isinstance(reviewed_fix, str) and reviewed_fix.strip():
                    if "```python" in reviewed_fix:
                        try:
                            reviewed_fix = re.search(r"```python\s*(.*?)\s*```", reviewed_fix, re.DOTALL).group(1).strip()
                            raw_func = re.search(r"def\s+(\w+)\s*\(.*?\):.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None)", reviewed_fix, re.DOTALL | re.MULTILINE)
                            if raw_func:
                                final_fix = raw_func.group(0).strip()
                            else:
                                logging.warning(f"Reviewed fix for {error_id} missing valid try/except—using original fix.")
                        except AttributeError:
                            logging.warning(f"Reviewed fix for {error_id} not in expected ```python``` format—using original fix.")
                    else:
                        raw_func = re.search(r"def\s+(\w+)\s*\(.*?\):.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None)", reviewed_fix, re.DOTALL | re.MULTILINE)
                        if raw_func:
                            final_fix = raw_func.group(0).strip()
                        else:
                            logging.warning(f"Reviewed fix for {error_id} missing valid try/except—using original fix.")

                # Debug: Log final fix
                logging.debug(f"Debug: Final fix for {error_id}: {final_fix}")

                # Stage and validate the fix
                fix_works = False
                fix_error = "No validation performed"
                if final_fix:
                    temp_script_path = script_path + ".tmp"
                    shutil.copy(script_path, temp_script_path)
                    with open(temp_script_path, "r") as f:
                        original_content = f.read()
                    with open(temp_script_path, "w") as f:
                        # Replace only the original function with final_fix
                        func_match = re.search(r"def\s+\w+\s*\(.*?\):.*?(?=\n\n|\Z)", original_content, re.DOTALL)
                        if func_match:
                            f.write(original_content.replace(func_match.group(0), final_fix) + "\n")
                        else:
                            f.write(final_fix + "\n" + original_content)

                    fix_works, fix_error = self.test_fix(temp_script_path, error)
                    if fix_works:
                        shutil.move(temp_script_path, script_path)
                        logging.info(f"Applied valid fix to {script_path}")
                    else:
                        os.remove(temp_script_path)
                        logging.warning(f"Fix for {error_id} failed validation: {fix_error}")

                blueprint_id = f"bp_fix_{error_id}"
                execution_trace_id = self.blueprint_executor.run_blueprint(
                    blueprint_id=blueprint_id,
                    task_name="Apply fix",
                    script_path=script_path,
                    execution_context=context,
                    final_fix=final_fix,
                    original_error=error
                )
                
                if execution_trace_id:
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
                        "attempts": attempt_count
                    }
                    self.log_entry("debugging_logs", error_id, log_entry)
                    
                    reindex_single_file(script_path, self.collections["project_codebase"], self.embed_model)
                    logging.info(f"Reindexed {script_path}")
                    
                    logs = [l if l["id"] != error_id else log_entry for l in logs]
                    with open(self.debug_log_file, "w") as f:
                        json.dump(logs, f, indent=4)

            if attempt_count >= self.max_attempts:
                logging.error("Max attempts reached for unresolved issues—exiting.")
                break

        self.reset_state()
        logging.info("Completed run and reset state for next test.")

if __name__ == "__main__":
    agent = BuildAgent(test_mode=True)
    agent.run()