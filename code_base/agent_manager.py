import requests
import re
import os
import ast
from code_base.network_utils import detect_api_url

class AgentManager:
    """Manages AI Agents for architecture, coding, review, and automation with simplified prompts and lighter models."""

    def __init__(self):
        self.agents = {
            "engineer": "codestral-22b-v0.1",
            "reviewer": "eaddario/deepseek-r1-distill-qwen-7b",
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

    def send_task(self, agent, task_prompt, timeout=300):
        model = self.agents.get(agent, "codestral-22b-v0.1")
        try:
            full_prompt = (
                f"{task_prompt}\n\n"
                "Output MUST be a complete Python function inside ```python ... ``` ONLY. "
                "NO prose, NO <think> blocks, NO test cases, NO comments (#), NO standalone raise statements outside try—strictly code. "
                "Use try/except for ZeroDivisionError or KeyError ONLY (use 'except (ZeroDivisionError, KeyError)' syntax, not '|'), "
                "return None in except, no returns outside except."
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
            # Strip all prose after code, not just <think>
            code_match = re.search(r"```(?:python)?\s*(.*?)\s*```", response_text, re.DOTALL)
            if code_match:
                response_text = code_match.group(0)  # Keep only the code block
            else:
                response_text = re.sub(r"<think>.*?</think>|\s*This solution:.*$", "", response_text, flags=re.DOTALL).strip()
            print(f"Raw response from {agent} ({model}): {response_text}")
            return response_text if response_text else f"❌ Empty response from {agent} ({model})."
        except requests.exceptions.Timeout:
            return f"❌ Timeout: {agent} ({model}) - {timeout}s"
        except requests.exceptions.RequestException as e:
            return f"❌ API Error: {agent} ({model}) - {e}"

    def review_task(self, codestral_output, timeout=300):
        review_prompt = (
            f"Review this: {codestral_output}. Return ONLY the COMPLETE fixed function in Python "
            "using a FULL try/except block for ZeroDivisionError or KeyError ONLY (use 'except (ZeroDivisionError, KeyError)' syntax, not '|'), "
            "returning None, inside ```python ... ```. NO prose, NO <think> blocks, NO extra logic, NO comments (#), NO standalone raise statements outside try, NO returns outside except."
        )
        return self.send_task("reviewer", review_prompt, timeout)

    def preprocess_ai_response(self, ai_response):
        if self.retry_count >= self.max_retries:
            print(f"⚠️ Max retries reached. Using fallback.")
            return "def placeholder():\n    pass"
        
        if not ai_response or ai_response.startswith("❌"):
            print(f"⚠️ Preprocessing failed: Empty or error:\n{ai_response}")
            self.retry_count += 1
            return None
        
        if "<think>" in ai_response:
            print(f"⚠️ Preprocessing warning: <think> detected in:\n{ai_response}")
            self.retry_count += 1
            return None

        # Extract code block with flexible markdown
        code_block = re.search(r"```(?:python)?\s*(.*?)\s*```", ai_response, re.DOTALL)
        if not code_block:
            print(f"⚠️ No code block found in:\n{ai_response}")
            self.retry_count += 1
            return None
        code = code_block.group(1).strip()

        # Validate using AST
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
                                # Check for ZeroDivisionError or KeyError (single, tuple, or union with '|')
                                if isinstance(handler.type, ast.Name):
                                    if handler.type.id in ["ZeroDivisionError", "KeyError"]:
                                        has_valid_except = True
                                elif isinstance(handler.type, ast.Tuple):
                                    if all(isinstance(elt, ast.Name) and elt.id in ["ZeroDivisionError", "KeyError"] for elt in handler.type.elts):
                                        has_valid_except = True
                                elif isinstance(handler.type, ast.BinOp) and isinstance(handler.type.op, ast.BitOr):
                                    left = handler.type.left
                                    right = handler.type.right
                                    if (isinstance(left, ast.Name) and left.id in ["ZeroDivisionError", "KeyError"] and 
                                        isinstance(right, ast.Name) and right.id in ["ZeroDivisionError", "KeyError"]):
                                        has_valid_except = True
                                # Check return None in except
                                for stmt in handler.body:
                                    if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                                        has_return_none = True
                            # Allow Raise, returns, and expressions in try block
                            for stmt in body_node.body:
                                if isinstance(stmt, (ast.Return, ast.Raise, ast.Expr)):
                                    continue  # Valid in try (comments, raises, returns)
                        # Check for standalone Raise outside Try (reject)
                        elif isinstance(body_node, ast.Raise):
                            print(f"⚠️ Standalone raise statement found outside try/except in:\n{code}")
                            self.retry_count += 1
                            return None
                    # Check for prose or invalid structure (reject Str nodes outside Try)
                    if any(isinstance(n, ast.Expr) and isinstance(n.value, ast.Str) for n in node.body if not isinstance(n, ast.Try)):
                        print(f"⚠️ Prose detected in function body:\n{code}")
                        self.retry_count += 1
                        return None
                    if has_function and has_valid_try and has_valid_except and has_return_none:
                        self.retry_count = 0
                        return code
            if not has_function:
                print(f"⚠️ No function definition found in:\n{code}")
                self.retry_count += 1
                return None
            print(f"⚠️ Missing try/except, invalid exceptions, or missing returns in:\n{code}")
            self.retry_count += 1
            return None
        except SyntaxError:
            print(f"⚠️ Invalid Python syntax in:\n{code}")
            self.retry_count += 1
            return None

    def delegate_task(self, agent, task_description, save_to=None, timeout=300):
        print(f"🔹 Sending task to {agent}: {task_description} (Timeout: {timeout}s)")
        result = self.send_task(agent, task_description, timeout)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            print(f"❌ Invalid response for {agent}. Retrying...")
            result = self.send_task(agent, task_description, timeout + 60)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            print(f"❌ Still invalid. Last try with strict mode...")
            result = self.send_task(
                agent,
                f"STRICT MODE: {task_description}\nRespond with code in ```python ... ``` or 'ERROR: No response.'",
                timeout + 60
            )
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌") or result == "ERROR: No response.":
            print("❌ Using fallback after max retries.")
            self.retry_count = 0
            return "def placeholder():\n    pass"
        
        if any(prose in result.lower() for prose in ["here's", "here is", "corrected", "fixed", "modified", "<think>"]):
            reviewed_fix = self.review_task(result, timeout)
            if reviewed_fix and isinstance(reviewed_fix, str) and reviewed_fix.strip() and reviewed_fix != "ERROR: No valid function found.":
                final_fix = self.preprocess_ai_response(reviewed_fix)
            else:
                print(f"❌ Review failed—using original.")
                final_fix = self.preprocess_ai_response(result)
        else:
            final_fix = self.preprocess_ai_response(result)
        
        if final_fix is None:
            print("❌ Preprocessing failed. Using fallback.")
            self.retry_count = 0
            return "def placeholder():\n    pass"
        
        self.retry_count = 0
        return final_fix

if __name__ == "__main__":
    agent_manager = AgentManager()
    response = agent_manager.delegate_task("engineer", "Fix a ZeroDivisionError in test_script.py: ```python\ndef divide(a, b):\n    return a / b\n```")
    print(f"✅ Agent Response:\n{response}")