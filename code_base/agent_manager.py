import requests
import re
import os
import ast
import subprocess
import traceback
import sys
import logging
from io import StringIO
from code_base.network_utils import detect_api_url
from code_base.test_case_generator import get_error_handler  # Import the new test case generator

# Configure logging for agent_manager.py
try:
    log_dir = "/mnt/f/projects/ai-recall-system/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"{log_dir}/agent_manager_debug.log", mode='a')
        ]
    )
    logging.debug("Logging initialized successfully for agent_manager.py")
    with open(f"{log_dir}/agent_manager_debug.log", "a") as f:
        f.write("Test write to verify file handler\n")
except Exception as e:
    print(f"⚠️ Failed to initialize logging for agent_manager.py: {e}")
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.warning("Falling back to console-only logging due to file handler error")

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

    def test_fix(self, script_path, original_error, stack_trace, fix):
        """Test if the fix handles the original error using AST for parsing and modification."""
        logging.debug(f"Starting test_fix for script_path: {script_path}, original_error: {original_error}, stack_trace: {stack_trace}")
        try:
            with open(script_path, "r") as f:
                script_content = f.read()
            logging.debug(f"Original script content: {script_content}")

            # Parse the script into an AST
            tree = ast.parse(script_content)
            logging.debug("Parsed script into AST")

            # Extract the line number from the stack_trace
            line_match = re.search(r"line (\d+)", stack_trace)
            if not line_match:
                logging.error("Could not extract line number from stack_trace")
                return False, "Invalid stack_trace format"
            error_line = int(line_match.group(1))
            logging.debug(f"Error line from stack_trace: {error_line}")

            # Find the function containing the error line
            target_func = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.lineno <= error_line <= node.end_lineno:
                        target_func = node
                        break
            if not target_func:
                logging.error("No function found containing the error line")
                return False, "No function found at error line"

            func_name = target_func.name
            logging.debug(f"Found target function: {func_name} at lines {target_func.lineno}-{target_func.end_lineno}")

            # Parse the AI-generated fix and apply it to the target function
            fix_tree = ast.parse(fix)
            if not fix_tree.body or not isinstance(fix_tree.body[0], ast.FunctionDef):
                logging.error("Fix does not contain a valid function definition")
                return False, "Invalid fix format"
            fix_func = fix_tree.body[0]
            if fix_func.name != func_name:
                logging.error(f"Fix function name {fix_func.name} does not match target function {func_name}")
                return False, "Fix function name mismatch"
            target_func.body = fix_func.body  # Replace the body of the target function with the fixed body
            logging.debug(f"Applied fix to function {func_name}")

            # Extract argument names for dynamic test case generation
            arg_names = [arg.arg for arg in target_func.args.args]

            # Get the error handler for the original error
            handler = get_error_handler(original_error)

            # Generate test case dynamically
            self.test_input, self.expected_result = handler.generate_test_case(arg_names)  # Store as instance attributes
            if self.test_input is None:
                logging.error(f"No test case defined for {original_error}")
                return False, f"No test case for {original_error}"

            # Generate the test call
            test_call = f"{func_name}({', '.join(map(str, self.test_input))})"

            # Create a new module AST for the test script
            test_module = ast.Module(body=[
                ast.Import(names=[ast.alias(name='sys', asname=None)]),
                ast.ImportFrom(module='io', names=[ast.alias(name='StringIO', asname=None)], level=0),
                target_func,
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
            logging.debug(f"Generated test code: {test_code}")

            temp_test_path = script_path + ".test"
            with open(temp_test_path, "w") as f:
                f.write(test_code)
            logging.debug(f"Wrote test script to: {temp_test_path}")

            try:
                process = subprocess.run(
                    ["python", temp_test_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                logging.debug(f"Subprocess completed: returncode={process.returncode}, stdout={process.stdout}, stderr={process.stderr}")
            except subprocess.TimeoutExpired as e:
                logging.error(f"Subprocess timeout: {e}")
                if os.path.exists(temp_test_path):
                    os.remove(temp_test_path)
                    logging.debug(f"Cleaned up test script after timeout: {temp_test_path}")
                return False, "Timeout: Script hung"
            except subprocess.SubprocessError as e:
                logging.error(f"Subprocess error: {e}, traceback: {traceback.format_exc()}")
                if os.path.exists(temp_test_path):
                    os.remove(temp_test_path)
                    logging.debug(f"Cleaned up test script after subprocess error: {temp_test_path}")
                return False, f"Subprocess error: {str(e)}"

            if os.path.exists(temp_test_path):
                os.remove(temp_test_path)
                logging.debug(f"Cleaned up test script: {temp_test_path}")

            output = process.stdout.strip()
            logging.debug(f"Subprocess output: {output}")
            if "Test result: Success" in output:
                logging.debug("Fix validated successfully")
                return True, ""
            else:
                error_msg = process.stderr or "Fix did not handle the original error"
                logging.debug(f"Fix validation failed: {error_msg}")
                return False, error_msg

        except Exception as e:
            logging.error(f"Error in test_fix: {e}, traceback: {traceback.format_exc()}")
            if 'temp_test_path' in locals() and os.path.exists(temp_test_path):
                os.remove(temp_test_path)
                logging.debug(f"Cleaned up test script after error: {temp_test_path}")
            return False, f"Test execution failed: {str(e)}"

    def send_task(self, agent, task_prompt, timeout=300):
        model = self.agents.get(agent, "codestral-22b-v0.1")
        logging.debug(f"Sending task to {agent} ({model}) with prompt: {task_prompt}")
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
            logging.debug(f"Received response: {response_text}")
            return response_text if response_text else f"❌ Empty response from {agent} ({model})."
        except requests.exceptions.Timeout:
            logging.error(f"Request timeout: {agent} ({model}) - {timeout}s")
            return f"❌ Timeout: {agent} ({model}) - {timeout}s"
        except requests.exceptions.RequestException as e:
            logging.error(f"API error: {agent} ({model}) - {e}")
            return f"❌ API Error: {agent} ({model}) - {e}"

    def review_task(self, codestral_output, timeout=300):
        logging.debug(f"Reviewing codestral output: {codestral_output}")
        review_prompt = (
            f"Review this: {codestral_output}. Return ONLY the COMPLETE fixed function in Python "
            "using a FULL try/except block for ZeroDivisionError or KeyError ONLY, returning None in except, "
            "inside ```python ... ```. NO prose, NO <think> blocks, NO extra logic, NO comments (#), "
            "NO standalone raise statements outside try, NO returns outside except. STRICT ADHERENCE REQUIRED."
        )
        return self.send_task("reviewer", review_prompt, timeout)

    def preprocess_ai_response(self, ai_response):
        logging.debug(f"Preprocessing AI response: {ai_response}")
        if self.retry_count >= self.max_retries:
            logging.warning(f"Max retries reached. Using fallback.")
            return "def placeholder():\n    pass"
        
        if not ai_response or ai_response.startswith("❌"):
            logging.warning(f"Preprocessing failed: Empty or error:\n{ai_response}")
            self.retry_count += 1
            return None
        
        if "<think>" in ai_response or any(prose in ai_response.lower() for prose in ["here's", "here is", "corrected", "fixed", "modified"]):
            logging.warning(f"Prohibited content detected in:\n{ai_response}")
            self.retry_count += 1
            return None

        code_block = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", ai_response, re.DOTALL)
        if not code_block:
            logging.warning(f"No code block found in:\n{ai_response}")
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
                            logging.warning(f"Standalone raise statement found outside try/except in:\n{code}")
                            self.retry_count += 1
                            return None
                    if any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Str) for n in node.body if not isinstance(n, ast.Try)):
                        logging.warning(f"Prose detected in function body:\n{code}")
                        self.retry_count += 1
                        return None
                    if has_function and has_valid_try and has_valid_except and has_return_none:
                        self.retry_count = 0
                        logging.debug(f"Preprocessing successful, returning code: {code}")
                        return code
            if not has_function:
                logging.warning(f"No function definition found in:\n{code}")
                self.retry_count += 1
                return None
            logging.warning(f"Missing try/except, invalid exceptions, or missing returns in:\n{code}")
            self.retry_count += 1
            return None
        except SyntaxError as e:
            logging.warning(f"Invalid Python syntax in:\n{code}, error: {e}")
            self.retry_count += 1
            return None

    def delegate_task(self, agent, task_description, save_to=None, timeout=300):
        logging.debug(f"Sending task to {agent}: {task_description} (Timeout: {timeout}s)")
        print(f"🔹 Sending task to {agent}: {task_description} (Timeout: {timeout}s)")
        result = self.send_task(agent, task_description, timeout)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            logging.warning(f"Invalid response for {agent}. Retrying...")
            print(f"❌ Invalid response for {agent}. Retrying...")
            result = self.send_task(agent, task_description, timeout + 60)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            logging.warning(f"Still invalid. Last try with strict mode...")
            print(f"❌ Still invalid. Last try with strict mode...")
            result = self.send_task(
                agent,
                f"STRICT MODE: {task_description}\nRespond with ONLY a complete Python function in ```python ... ``` or 'ERROR: No response.'",
                timeout + 60
            )
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌") or result == "ERROR: No response.":
            logging.error("Using fallback after max retries.")
            print("❌ Using fallback after max retries.")
            self.retry_count = 0
            return "def placeholder():\n    pass"
        
        if any(prose in result.lower() for prose in ["here's", "here is", "corrected", "fixed", "modified", "<think>"]):
            reviewed_fix = self.review_task(result, timeout)
            logging.debug(f"Reviewer response for task: {reviewed_fix}")
            print(f"Debug: Reviewer response for task: {reviewed_fix}")
            if reviewed_fix and isinstance(reviewed_fix, str) and reviewed_fix.strip() and reviewed_fix != "ERROR: No valid function found.":
                final_fix = self.preprocess_ai_response(reviewed_fix)
            else:
                logging.warning(f"Review failed—using original.")
                print(f"❌ Review failed—using original.")
                final_fix = self.preprocess_ai_response(result)
        else:
            final_fix = self.preprocess_ai_response(result)
        
        if final_fix is None:
            logging.error("Preprocessing failed. Using fallback.")
            print("❌ Preprocessing failed. Using fallback.")
            self.retry_count = 0
            return "def placeholder():\n    pass"
        
        self.retry_count = 0
        logging.debug(f"Task completed successfully, final fix: {final_fix}")
        return final_fix

if __name__ == "__main__":
    agent_manager = AgentManager()
    response = agent_manager.delegate_task("engineer", "Fix a ZeroDivisionError in test_script.py: ```python\ndef divide(a, b):\n    return a / b\n```")
    print(f"✅ Agent Response:\n{response}")