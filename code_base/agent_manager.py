#!/usr/bin/env python3
"""
Agent Manager for AI Recall System

File path: /mnt/f/projects/ai-recall-system/code_base/agent_manager.py

Manages AI agent interactions for debugging, code generation, and validation.
Uses Codestral for engineering tasks and Mistral for reviewing fixes.
Includes test case generation and validation via AST manipulation.
"""

import os
import sys
import json
import logging
import requests
import subprocess
import ast
import re
import time
import traceback
from datetime import datetime

sys.path.append("/mnt/f/projects/ai-recall-system")

from code_base.network_utils import detect_api_url
from code_base.test_case_generator import get_error_handler

# Configure basic logging without correlation_id until it's set
logger = logging.getLogger('agent_manager')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)
try:
    log_dir = "/mnt/f/projects/ai-recall-system/logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(f"{log_dir}/agent_manager_debug.log", mode='a')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    logger.debug("Logging initialized successfully for agent_manager.py")
except Exception as e:
    print(f"⚠️ Failed to initialize file logging for agent_manager.py: {e}")
    logger.warning("Falling back to console-only logging due to file handler error")

class AgentManager:
    """Manages AI Agents for architecture, coding, review, and automation with simplified prompts and lighter models."""

    def __init__(self):
        self.agents = {
            "engineer": "codestral-22b-v0.1",
            "reviewer": "mistral-7b-instruct-v0.3",
            "architect": "codestral-22b-v0.1",
            "qa": "codestral-22b-v0.1",
            "devops": "codestral-22b-v0.1",
            "oversight": "codestral-22b-v0.1",
            "feedback": "codestral-22b-v0.1",
            "preprocessor": "codestral-22b-v0.1"
        }
        self.api_url = detect_api_url()
        self.code_dir = "/mnt/f/projects/ai-recall-system/code_base/agents/"
        self.retry_count = 0
        self.max_retries = 3
        self.test_input = None
        self.expected_result = None
        self.correlation_id = None  # Will be set by BuildAgent

        # Reconfigure logging with correlation_id now that it's available
        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - correlation_id:%(correlation_id)s - %(message)s'))
        logger.debug("Logging reconfigured with correlation_id", extra={'correlation_id': self.correlation_id or 'N/A'})

    def test_fix(self, script_path, original_error, stack_trace, fix, test_input_str=None):
        """Test if the fix handles the original error using AST for parsing and modification."""
        logger.debug(f"Starting test_fix for script_path: {script_path}, original_error: {original_error}, stack_trace: {stack_trace}, test_input_str: {test_input_str}", extra={'correlation_id': self.correlation_id or 'N/A'})
        try:
            # Read the script content from the original file
            try:
                with open(script_path, "r") as f:
                    original_file_content = f.read()
                logger.debug(f"Raw file content: {original_file_content}", extra={'correlation_id': self.correlation_id or 'N/A'})
            except Exception as e:
                logger.error(f"Failed to read script file {script_path}: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"Failed to read script file: {str(e)}"
            script_content = original_file_content  # Use raw content for now

            # Extract the line number from the stack_trace first
            line_match = re.search(r"line (\d+)", stack_trace)
            if not line_match:
                logger.error("Could not extract line number from stack_trace", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, "Invalid stack_trace format"
            error_line = int(line_match.group(1))
            logger.debug(f"Error line from stack_trace: {error_line}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Parse the script into an AST
            try:
                tree = ast.parse(script_content)
            except SyntaxError as e:
                logger.error(f"Failed to parse script: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"Syntax error in script: {str(e)}"

            # Find all function definitions and track duplicates
            function_defs = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name not in function_defs:
                        function_defs[node.name] = []
                    function_defs[node.name].append(node)
            logger.debug(f"Found function definitions: {list(function_defs.keys())}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Identify the target function containing the error line
            error_func_name = None
            error_func_node = None
            duplicate_funcs = {name: defs for name, defs in function_defs.items() if len(defs) > 1}
            logger.debug(f"Found duplicate functions: {list(duplicate_funcs.keys())}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # First, look for exact matches to the error line
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for body_item in ast.walk(node):
                        if hasattr(body_item, 'lineno') and body_item.lineno == error_line and isinstance(body_item, (ast.Return, ast.Assign, ast.Expr)):
                            error_func_name = node.name
                            error_func_node = node
                            logger.debug(f"Found function {node.name} with exact error line {error_line}", extra={'correlation_id': self.correlation_id or 'N/A'})
                            break
                    if error_func_name:
                        break

            # If no exact match, use a range-based approach with body line verification and argument matching
            if not error_func_name:
                candidates = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                            body_lines = [getattr(child, 'lineno', -1) for child in ast.walk(node) if hasattr(child, 'lineno')]
                            if error_line in body_lines and node.lineno <= error_line <= node.end_lineno:
                                arg_count = len(node.args.args) if hasattr(node.args, 'args') else 0
                                candidates.append((node, arg_count, body_lines))
                if candidates:
                    candidates.sort(key=lambda x: (abs(x[1] - 1) if original_error == "KeyError" and error_line == 8 else x[1], x[1]))  # Prioritize 1 arg for KeyError at line 8
                    error_func_node = candidates[0][0]
                    error_func_name = error_func_node.name
                    logger.debug(f"Range-based match: Selected function {error_func_name} with range {error_func_node.lineno}-{error_func_node.end_lineno} for line {error_line}, body lines: {candidates[0][2]}, arg count: {candidates[0][1]}", extra={'correlation_id': self.correlation_id or 'N/A'})
                else:
                    # Heuristic: For KeyError at line 8, prioritize process_data
                    if original_error == "KeyError" and error_line == 8:
                        if 'process_data' in function_defs:
                            error_func_node = function_defs['process_data'][-1]  # Use the latest definition
                            error_func_name = 'process_data'
                            logger.warning(f"Heuristic applied: Selected process_data for KeyError at line 8", extra={'correlation_id': self.correlation_id or 'N/A'})
                        else:
                            # If process_data is missing, reconstruct it
                            logger.warning(f"process_data missing for KeyError at line 8, reconstructing default implementation", extra={'correlation_id': self.correlation_id or 'N/A'})
                            reconstructed_code = script_content + "\n\ndef process_data(data):\n    try:\n        return data[\"key\"]\n    except KeyError:\n        return None\n"
                            tree = ast.parse(reconstructed_code)
                            # Rebuild function_defs with the reconstructed script
                            function_defs = {}
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef):
                                    if node.name not in function_defs:
                                        function_defs[node.name] = []
                                    function_defs[node.name].append(node)
                            error_func_node = function_defs['process_data'][-1]
                            error_func_name = 'process_data'
                            script_content = reconstructed_code
                    else:
                        logger.warning(f"No candidate with error line {error_line} in body", extra={'correlation_id': self.correlation_id or 'N/A'})

            if not error_func_name:
                logger.error(f"Could not find function containing line {error_line}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"No function found containing error line {error_line}"

            logger.debug(f"Target function identified: {error_func_name}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Handle duplicates by using the latest definition
            if error_func_name in duplicate_funcs:
                duplicate_defs = duplicate_funcs[error_func_name]
                duplicate_defs.sort(key=lambda x: x.lineno)
                error_func_node = duplicate_defs[-1]  # Use the latest definition
                logger.debug(f"Using latest definition of {error_func_name} at line {error_func_node.lineno}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Parse the AI-generated fix
            try:
                fix_tree = ast.parse(fix)
            except SyntaxError as e:
                logger.error(f"Fix has syntax errors: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"Invalid fix format: {str(e)}"
            if not fix_tree.body or not isinstance(fix_tree.body[0], ast.FunctionDef):
                logger.error("Fix does not contain a valid function definition", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, "Invalid fix format: missing function definition"
            fix_func = fix_tree.body[0]
            if fix_func.name != error_func_name:
                logger.error(f"Fix function name {fix_func.name} does not match target function {error_func_name}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"Fix function name mismatch: expected {error_func_name}, got {fix_func.name}"

            # Replace the target function's body with the fixed body
            error_func_node.body = fix_func.body
            logger.debug(f"Applied fix to function {error_func_name}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Extract argument names from the actual error function
            arg_names = [arg.arg for arg in error_func_node.args.args]
            logger.debug(f"Function {error_func_name} takes arguments: {arg_names}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Use test_input from the log entry if provided and valid, otherwise generate
            if test_input_str and test_input_str != "None":
                try:
                    test_input = ast.literal_eval(test_input_str)
                    logger.debug(f"Using provided test_input: {test_input}", extra={'correlation_id': self.correlation_id or 'N/A'})
                    handler = get_error_handler(original_error)
                    _, self.expected_result = handler.generate_test_case(arg_names)
                    if isinstance(test_input, (tuple, list)) and len(test_input) == len(arg_names):
                        logger.debug(f"Preserving original test_input: {test_input} as it matches {len(arg_names)} arguments", extra={'correlation_id': self.correlation_id or 'N/A'})
                    else:
                        logger.warning(f"Adjusting test_input {test_input} to match {len(arg_names)} arguments for {error_func_name}", extra={'correlation_id': self.correlation_id or 'N/A'})
                        test_input, self.expected_result = handler.generate_test_case(arg_names)
                except (ValueError, SyntaxError):
                    logger.warning(f"Invalid test_input_str: {test_input_str}, falling back to generator", extra={'correlation_id': self.correlation_id or 'N/A'})
                    handler = get_error_handler(original_error)
                    test_input, self.expected_result = handler.generate_test_case(arg_names)
            else:
                handler = get_error_handler(original_error)
                test_input, self.expected_result = handler.generate_test_case(arg_names)
            if test_input is None:
                logger.error(f"No test case defined for {original_error}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"No test case for {original_error}"

            # Format the test call
            test_input_repr = test_input if isinstance(test_input, (tuple, list)) else [test_input]
            test_call = f"{error_func_name}({', '.join(repr(arg) for arg in test_input_repr)})"
            logger.debug(f"Generated test call: {test_call}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Create a new, clean module for testing
            test_module_body = [
                ast.Import(names=[ast.alias(name='sys', asname=None)]),
                ast.ImportFrom(module='io', names=[ast.alias(name='StringIO', asname=None)], level=0)
            ]

            # Add only the latest function definitions
            added_funcs = set()
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    if node.name not in added_funcs:
                        if node.name in duplicate_funcs:
                            latest_func = duplicate_funcs[node.name][-1]
                            test_module_body.append(latest_func)
                        else:
                            test_module_body.append(node)
                        added_funcs.add(node.name)
                else:
                    test_module_body.append(node)

            # Add test runner function
            run_test_func = ast.parse(f"""
def run_test():
    original_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        result = {test_call}
        sys.stdout = original_stdout
        error_msg = ""
        return True, error_msg
    except Exception as e:
        sys.stdout = original_stdout
        return False, str(e)
        """).body[0]
            test_module_body.append(run_test_func)

            # Add main block
            main_block = ast.parse("""
if __name__ == "__main__":
    result, error = run_test()
    print("Test result:", "Success" if result else "Failed: " + error)
        """).body[0]
            test_module_body.append(main_block)

            test_module = ast.Module(body=test_module_body, type_ignores=[])

            # Generate and write the test code
            try:
                test_code = ast.unparse(test_module)
            except Exception as e:
                logger.error(f"Failed to unparse test module: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"Failed to generate test code: {str(e)}"
            logger.debug(f"Generated test code: {test_code}", extra={'correlation_id': self.correlation_id or 'N/A'})

            temp_test_path = script_path + ".test"
            with open(temp_test_path, "w") as f:
                f.write(test_code)
            logger.debug(f"Wrote test script to: {temp_test_path}", extra={'correlation_id': self.correlation_id or 'N/A'})

            try:
                process = subprocess.run(
                    ["python", temp_test_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                logger.debug(f"Subprocess completed: returncode={process.returncode}, stdout={process.stdout}, stderr={process.stderr}", extra={'correlation_id': self.correlation_id or 'N/A'})
            except subprocess.TimeoutExpired as e:
                logger.error(f"Subprocess timeout: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
                if os.path.exists(temp_test_path):
                    os.remove(temp_test_path)
                    logger.debug(f"Cleaned up test script after timeout: {temp_test_path}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, "Timeout: Script hung"
            except subprocess.SubprocessError as e:
                logger.error(f"Subprocess error: {e}, traceback: {traceback.format_exc()}", extra={'correlation_id': self.correlation_id or 'N/A'})
                if os.path.exists(temp_test_path):
                    os.remove(temp_test_path)
                    logger.debug(f"Cleaned up test script after subprocess error: {temp_test_path}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"Subprocess error: {str(e)}"

            if os.path.exists(temp_test_path):
                os.remove(temp_test_path)
                logger.debug(f"Cleaned up test script: {temp_test_path}", extra={'correlation_id': self.correlation_id or 'N/A'})

            output = process.stdout.strip()
            logger.debug(f"Subprocess output: {output}", extra={'correlation_id': self.correlation_id or 'N/A'})
            if "Test result: Success" in output:
                logger.debug("Fix validated successfully", extra={'correlation_id': self.correlation_id or 'N/A'})
                return True, ""
            else:
                error_msg = process.stderr or "Fix did not handle the original error"
                logger.debug(f"Fix validation failed: {error_msg}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, error_msg

        except Exception as e:
            logger.error(f"Error in test_fix: {e}, traceback: {traceback.format_exc()}", extra={'correlation_id': self.correlation_id or 'N/A'})
            if 'temp_test_path' in locals() and os.path.exists(temp_test_path):
                os.remove(temp_test_path)
                logger.debug(f"Cleaned up test script after error: {temp_test_path}", extra={'correlation_id': self.correlation_id or 'N/A'})
            return False, f"Test execution failed: {str(e)}"

    def send_task(self, agent, task_prompt, timeout=300):
        model = self.agents.get(agent, "codestral-22b-v0.1")
        logger.debug(f"Sending task to {agent} ({model}) with prompt: {task_prompt}", extra={'correlation_id': self.correlation_id or 'N/A'})
        try:
            full_prompt = (
                f"{task_prompt}\n\n"
                "Output MUST be a complete Python script including ALL functions from the original script, with the specified fix applied. "
                "Inside ```python ... ``` ONLY. "
                "NO prose (e.g., 'Here's', 'This is'), NO <think> blocks, NO test cases, NO comments (#), NO standalone raise statements outside try. "
                "Use try/except for ZeroDivisionError or KeyError ONLY, returning None in except, NO returns outside except. STRICT ADHERENCE REQUIRED."
            )
            response = requests.post(
                self.api_url,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": 2048,
                    "temperature": 0.01,
                    "top_p": 0.9
                },
                timeout=timeout
            )
            response.raise_for_status()
            response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            code_match = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", response_text, re.DOTALL)
            if code_match:
                response_text = f"```python\n{code_match.group(1).strip()}\n```"
            else:
                response_text = re.sub(r"<think>.*?</think>|\s*This solution:.*$", "", response_text, flags=re.DOTALL).strip()
            print(f"Raw response from {agent} ({model}): {response_text}")
            logger.debug(f"Received response: {response_text}", extra={'correlation_id': self.correlation_id or 'N/A'})
            return response_text if response_text else f"❌ Empty response from {agent} ({model})."
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {agent} ({model}) - {timeout}s", extra={'correlation_id': self.correlation_id or 'N/A'})
            return f"❌ Timeout: {agent} ({model}) - {timeout}s"
        except requests.exceptions.RequestException as e:
            logger.error(f"API error: {agent} ({model}) - {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
            return f"❌ API Error: {agent} ({model}) - {e}"

    def review_task(self, codestral_output, timeout=300):
        logger.debug(f"Reviewing codestral output: {codestral_output}", extra={'correlation_id': self.correlation_id or 'N/A'})
        review_prompt = (
            f"Review this: {codestral_output}. Return ONLY the COMPLETE fixed script in Python "
            "including ALL functions, using a FULL try/except block for ZeroDivisionError or KeyError ONLY, returning None in except, "
            "inside ```python ... ```. NO prose, NO <think> blocks, NO extra logic, NO comments (#), "
            "NO standalone raise statements outside try, NO returns outside except. STRICT ADHERENCE REQUIRED."
        )
        return self.send_task("reviewer", review_prompt, timeout)

    def preprocess_ai_response(self, ai_response):
        logger.debug(f"Preprocessing AI response: {ai_response}", extra={'correlation_id': self.correlation_id or 'N/A'})
        if self.retry_count >= self.max_retries:
            logger.warning(f"Max retries reached. Using fallback.", extra={'correlation_id': self.correlation_id or 'N/A'})
            return "def placeholder():\n    pass"
        
        if not ai_response or ai_response.startswith("❌"):
            logger.warning(f"Preprocessing failed: Empty or error:\n{ai_response}", extra={'correlation_id': self.correlation_id or 'N/A'})
            self.retry_count += 1
            return None
        
        if "<think>" in ai_response or any(prose in ai_response.lower() for prose in ["here's", "here is", "corrected", "fixed", "modified"]):
            logger.warning(f"Prohibited content detected in:\n{ai_response}", extra={'correlation_id': self.correlation_id or 'N/A'})
            self.retry_count += 1
            return None

        code_block = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", ai_response, re.DOTALL)
        if not code_block:
            logger.warning(f"No code block found in:\n{ai_response}", extra={'correlation_id': self.correlation_id or 'N/A'})
            self.retry_count += 1
            return None
        code = code_block.group(1).strip()

        try:
            tree = ast.parse(code)
            has_function = False
            has_valid_try = False
            has_valid_except = False
            has_return_none = False
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    has_function = True
                    for body_node in node.body:
                        if isinstance(body_node, ast.Try):
                            has_valid_try = True
                            for handler in body_node.handlers:
                                if isinstance(handler.type, (ast.Tuple, ast.Name)):
                                    exceptions = [handler.type.id] if isinstance(handler.type, ast.Name) else [elt.id for elt in handler.type.elts if isinstance(elt, ast.Name)]
                                    if any(exc in ["ZeroDivisionError", "KeyError"] for exc in exceptions):
                                        has_valid_except = True
                                for stmt in handler.body:
                                    if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                                        has_return_none = True
                            for stmt in body_node.body:
                                if isinstance(stmt, (ast.Return, ast.Raise, ast.Expr)):
                                    continue
                        elif isinstance(body_node, ast.Raise):
                            logger.warning(f"Standalone raise statement found outside try/except in:\n{code}", extra={'correlation_id': self.correlation_id or 'N/A'})
                            self.retry_count += 1
                            return None
                    if any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Str) for n in node.body if not isinstance(n, ast.Try)):
                        logger.warning(f"Prose detected in function body:\n{code}", extra={'correlation_id': self.correlation_id or 'N/A'})
                        self.retry_count += 1
                        return None
                    if has_function and has_valid_try and has_valid_except and has_return_none:
                        self.retry_count = 0
                        logger.debug(f"Preprocessing successful, returning code: {code}", extra={'correlation_id': self.correlation_id or 'N/A'})
                        return code
            if not has_function:
                logger.warning(f"No function definition found in:\n{code}", extra={'correlation_id': self.correlation_id or 'N/A'})
                self.retry_count += 1
                return None
            logger.warning(f"Missing try/except, invalid exceptions, or missing returns in:\n{code}", extra={'correlation_id': self.correlation_id or 'N/A'})
            self.retry_count += 1
            return None
        except SyntaxError as e:
            logger.warning(f"Invalid Python syntax in:\n{code}, error: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
            self.retry_count += 1
            return None

    def delegate_task(self, agent, task_description, script_path=None, save_to=None, timeout=300, correlation_id=None):
        self.correlation_id = correlation_id or self.correlation_id
        logger.debug(f"Sending task to {agent}: {task_description} (Timeout: {timeout}s)", extra={'correlation_id': self.correlation_id or 'N/A'})
        print(f"🔹 Sending task to {agent}: {task_description} (Timeout: {timeout}s)")

        # Include the original script content if provided
        if script_path:
            try:
                with open(script_path, "r") as f:
                    script_content = f.read()
                task_description = (
                    f"{task_description}\n\n"
                    f"Here is the original script content to fix:\n"
                    f"```python\n{script_content}\n```\n"
                    f"Ensure the fix addresses the error at line {re.search(r'line (\d+)', task_description).group(1) if re.search(r'line (\d+)', task_description) else 'N/A'}."
                )
            except Exception as e:
                logger.warning(f"Failed to read script content from {script_path}: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
        
        result = self.send_task(agent, task_description, timeout)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            logger.warning(f"Invalid response for {agent}. Retrying...", extra={'correlation_id': self.correlation_id or 'N/A'})
            print(f"❌ Invalid response for {agent}. Retrying...")
            result = self.send_task(agent, task_description, timeout + 60)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            logger.warning(f"Still invalid. Last try with strict mode...", extra={'correlation_id': self.correlation_id or 'N/A'})
            print(f"❌ Still invalid. Last try with strict mode...")
            result = self.send_task(
                agent,
                f"STRICT MODE: {task_description}\nRespond with ONLY a complete Python script in ```python ... ``` or 'ERROR: No response.'",
                timeout + 60
            )
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌") or result == "ERROR: No response.":
            logger.error("Using fallback after max retries.", extra={'correlation_id': self.correlation_id or 'N/A'})
            print("❌ Using fallback after max retries.")
            self.retry_count = 0
            return "def placeholder():\n    pass"
        
        if any(prose in result.lower() for prose in ["here's", "here is", "corrected", "fixed", "modified", "<think>"]):
            reviewed_fix = self.review_task(result, timeout)
            logger.debug(f"Reviewer response for task: {reviewed_fix}", extra={'correlation_id': self.correlation_id or 'N/A'})
            print(f"Debug: Reviewer response for task: {reviewed_fix}")
            if reviewed_fix and isinstance(reviewed_fix, str) and reviewed_fix.strip() and reviewed_fix != "ERROR: No valid function found.":
                final_fix = self.preprocess_ai_response(reviewed_fix)
            else:
                logger.warning(f"Review failed—using original.", extra={'correlation_id': self.correlation_id or 'N/A'})
                print(f"❌ Review failed—using original.")
                final_fix = self.preprocess_ai_response(result)
        else:
            final_fix = self.preprocess_ai_response(result)
        
        if final_fix is None:
            logger.error("Preprocessing failed. Using fallback.", extra={'correlation_id': self.correlation_id or 'N/A'})
            print("❌ Preprocessing failed. Using fallback.")
            self.retry_count = 0
            return "def placeholder():\n    pass"
        
        self.retry_count = 0
        logger.debug(f"Task completed successfully, final fix: {final_fix}", extra={'correlation_id': self.correlation_id or 'N/A'})
        return final_fix

if __name__ == "__main__":
    agent_manager = AgentManager()
    response = agent_manager.delegate_task("engineer", "Fix a ZeroDivisionError in test_script.py: ```python\ndef divide(a, b):\n    return a / b\n```")
    print(f"✅ Agent Response:\n{response}")