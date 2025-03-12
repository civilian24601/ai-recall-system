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
            # Read the script content
            try:
                with open(script_path, "r") as f:
                    script_content = f.read()
            except Exception as e:
                logger.error(f"Failed to read script file {script_path}: {e}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, f"Failed to read script file: {str(e)}"
            logger.debug(f"Original script content: {script_content}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Remove duplicate function definitions to avoid AST confusion
            functions = {}
            lines = script_content.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('def '):
                    func_name = line.split('def ')[1].split('(')[0].strip()
                    functions[func_name] = i

            # Keep only the latest definition of each function
            cleaned_lines = []
            seen = set()
            for i in range(len(lines) - 1, -1, -1):  # Iterate backwards to keep the latest definition
                line = lines[i]
                if line.strip().startswith('def '):
                    func_name = line.split('def ')[1].split('(')[0].strip()
                    if func_name not in seen:
                        seen.add(func_name)
                        cleaned_lines.insert(0, line)
                    continue
                cleaned_lines.insert(0, line)

            cleaned_content = '\n'.join(cleaned_lines)
            logger.debug(f"Cleaned script content: {cleaned_content}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Parse the cleaned script into an AST
            tree = ast.parse(cleaned_content)
            logger.debug("Parsed script into AST", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Extract the line number from the stack_trace
            line_match = re.search(r"line (\d+)", stack_trace)
            if not line_match:
                logger.error("Could not extract line number from stack_trace", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, "Invalid stack_trace format"
            error_line = int(line_match.group(1))
            logger.debug(f"Error line from stack_trace: {error_line}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Find the function containing the exact error line within its body
            target_func = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for item in node.body:
                        for child in ast.walk(item):
                            if hasattr(child, 'lineno') and child.lineno == error_line and isinstance(child, (ast.Return, ast.Assign, ast.Expr)):
                                target_func = node
                                logger.debug(f"Matched target function {node.name} with exact line {error_line} in body", extra={'correlation_id': self.correlation_id or 'N/A'})
                                break
                        if target_func:
                            break
                    if target_func:
                        break
            if not target_func:
                # Fallback to range-based matching with detailed logging
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.lineno <= error_line <= node.end_lineno:
                            target_func = node
                            logger.warning(f"Fallback: Matched target function {node.name} by range {node.lineno}-{node.end_lineno} for line {error_line}", extra={'correlation_id': self.correlation_id or 'N/A'})
                            # Log all body line numbers for debugging
                            body_lines = [child.lineno for child in ast.walk(node) if hasattr(child, 'lineno')]
                            logger.debug(f"Function {node.name} body lines: {body_lines}", extra={'correlation_id': self.correlation_id or 'N/A'})
                            # Verify error line is in body
                            if error_line not in body_lines:
                                logger.warning(f"Error line {error_line} not found in {node.name} body lines {body_lines}", extra={'correlation_id': self.correlation_id or 'N/A'})
                                target_func = None
                                continue
                            break
            if not target_func:
                logger.error("No function found containing the error line", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, "No function found at error line"

            func_name = target_func.name
            logger.debug(f"Found target function: {func_name} at lines {target_func.lineno}-{target_func.end_lineno}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Parse the AI-generated fix
            fix_tree = ast.parse(fix)
            if not fix_tree.body or not isinstance(fix_tree.body[0], ast.FunctionDef):
                logger.error("Fix does not contain a valid function definition", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, "Invalid fix format"
            fix_func = fix_tree.body[0]
            if fix_func.name != func_name:
                logger.error(f"Fix function name {fix_func.name} does not match target function {func_name}", extra={'correlation_id': self.correlation_id or 'N/A'})
                return False, "Fix function name mismatch"

            # Replace the target function's body with the fixed body
            target_func.body = fix_func.body
            logger.debug(f"Applied fix to function {func_name}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Extract argument names for dynamic test case generation
            arg_names = [arg.arg for arg in target_func.args.args]

            # Use test_input from the log entry if provided and valid, otherwise generate
            if test_input_str and test_input_str != "None":
                try:
                    test_input = ast.literal_eval(test_input_str)
                    logger.debug(f"Using provided test_input: {test_input}", extra={'correlation_id': self.correlation_id or 'N/A'})
                    handler = get_error_handler(original_error)
                    _, self.expected_result = handler.generate_test_case(arg_names)  # Ensure expected_result is set
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

            # Adjust test_input to match the number of arguments
            if isinstance(test_input, (tuple, list)):
                if len(arg_names) != len(test_input):
                    logger.warning(f"Adjusting test_input {test_input} to match {len(arg_names)} arguments for {func_name}", extra={'correlation_id': self.correlation_id or 'N/A'})
                    handler = get_error_handler(original_error)
                    test_input, self.expected_result = handler.generate_test_case(arg_names)
            test_call = f"{func_name}({', '.join(map(str, test_input) if isinstance(test_input, (tuple, list)) else [str(test_input)])})"
            logger.debug(f"Generated test call: {test_call}", extra={'correlation_id': self.correlation_id or 'N/A'})

            # Create a new module AST for the test script
            test_module = ast.Module(body=[
                ast.Import(names=[ast.alias(name='sys', asname=None)]),
                ast.ImportFrom(module='io', names=[ast.alias(name='StringIO', asname=None)], level=0),
            ] + list(tree.body) + [  # Include all functions from the original script
                ast.parse(f"""
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
                """).body[0],
                ast.parse("""
if __name__ == "__main__":
    result, error = run_test()
    print("Test result:", "Success" if result else "Failed: " + error)
                """).body[0]
            ], type_ignores=[])

            # Unparse the test script with correct formatting
            test_code = ast.unparse(test_module)
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
                "Output MUST be a complete Python function inside ```python ... ``` ONLY. "
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
            f"Review this: {codestral_output}. Return ONLY the COMPLETE fixed function in Python "
            "using a FULL try/except block for ZeroDivisionError or KeyError ONLY, returning None in except, "
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

    def delegate_task(self, agent, task_description, save_to=None, timeout=300, correlation_id=None):
        self.correlation_id = correlation_id or self.correlation_id
        logger.debug(f"Sending task to {agent}: {task_description} (Timeout: {timeout}s)", extra={'correlation_id': self.correlation_id or 'N/A'})
        print(f"🔹 Sending task to {agent}: {task_description} (Timeout: {timeout}s)")
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
                f"STRICT MODE: {task_description}\nRespond with ONLY a complete Python function in ```python ... ``` or 'ERROR: No response.'",
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