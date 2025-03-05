import requests
import re
import os
from code_base.network_utils import detect_api_url

class AgentManager:
    """Manages AI Agents for architecture, coding, review, and automation with simplified prompts and lighter models."""

    def __init__(self):
        """Initialize agents and set API URL."""
        self.agents = {
            "engineer": "codestral-22b-v0.1",  # Primary for fixes
            "reviewer": "deepseek-r1-distill-qwen-7b",  # DeepSeek Qwen 7B for faster review
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
            # Stricter prompt to enforce ```python ... ```
            full_prompt = (
                f"{task_prompt}\n\n"
                "Output MUST be a complete Python function inside ```python ... ``` with NO prose, NO <think> blocks, NO test cases."
            )
            response = requests.post(
                self.api_url,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": full_prompt}],
                    "max_tokens": 1024,
                    "temperature": 0.05,
                    "stop": ["```"]
                },
                timeout=timeout
            )
            response.raise_for_status()
            response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            print(f"Raw response from {agent} ({model}): {response_text}")
            return response_text if response_text else f"❌ Empty response from {agent} ({model})."
        except requests.exceptions.Timeout:
            return f"❌ Timeout: {agent} ({model}) did not respond in {timeout} seconds."
        except requests.exceptions.RequestException as e:
            return f"❌ API Error: {agent} ({model}) - {e}"

    def review_task(self, codestral_output, timeout=300):
        review_prompt = (
            f"Please review this response: {codestral_output}. Strip all prose, test cases, <think> blocks, and irrelevant code. "
            "Return ONLY the COMPLETE fixed function in Python using a FULL try/except block with the appropriate except clause to handle the error (e.g., ZeroDivisionError, KeyError), returning None, with NO extra logic, NO prose, and NO explanations, inside ```python ... ```. "
            "Use few-shot examples:\n"
            "Example 1: Input 'Here’s a fix: def divide(a, b): return a / b' → Output '```python\ndef divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return None\n```'\n"
            "Example 2: Input 'Here’s a fix: def authenticate(user_data): return user_data[\"username\"]' → Output '```python\ndef authenticate(user_data):\n    try:\n        return user_data[\"username\"]\n    except KeyError:\n        return None\n```'\n"
            "Respond with code or 'ERROR: No valid function found.' only."
        )
        return self.send_task("reviewer", review_prompt, timeout)

    def preprocess_ai_response(self, ai_response):
        if self.retry_count >= self.max_retries:
            print(f"⚠️ Max retries reached. Using fallback.")
            return "def placeholder():\n    pass"
        
        if not ai_response or ai_response.startswith("❌") or ai_response == "ERROR: No valid function found.":
            print(f"⚠️ Preprocessing failed: Empty or error response:\n{ai_response}")
            self.retry_count += 1
            return None
        
        # Handle <think> or malformed output
        if "<think>" in ai_response:
            print(f"⚠️ Preprocessing warning: <think> block detected in:\n{ai_response}")
            self.retry_count += 1
            return None

        code_block = re.search(r"```python\s*(.*?)\s*```", ai_response, re.DOTALL)
        if code_block:
            code = code_block.group(1).strip()
        else:
            raw_func = re.search(r"(def\s+\w+$$ .*? $$:.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None))", ai_response, re.DOTALL | re.MULTILINE)
            if raw_func:
                code = raw_func.group(1).strip()
            else:
                print(f"⚠️ Preprocessing failed: No valid function in:\n{ai_response}")
                self.retry_count += 1
                return None

        if ("try:" in code and "except" in code and "return None" in code and 
            any(error in code for error in ["ZeroDivisionError", "KeyError"]) and 
            not any(prose in code.lower() for prose in ["test case", "simulated", "<think>"]) and 
            "except:" not in code):
            self.retry_count = 0
            return code
        print(f"⚠️ Preprocessing warning: Invalid function in:\n{code}")
        self.retry_count += 1
        return None

    def delegate_task(self, agent, task_description, save_to=None, timeout=300):
        print(f"🔹 Sending task to {agent}: {task_description} (Timeout: {timeout}s)")
        result = self.send_task(agent, task_description, timeout)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            print(f"❌ AI response invalid for {agent}. Retrying...")
            result = self.send_task(agent, task_description, timeout + 60)
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌"):
            print(f"❌ Still invalid. Last try with strict mode...")
            result = self.send_task(
                agent,
                f"STRICT MODE: {task_description}\nRespond with code or 'ERROR: No response.' only.",
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
    response = agent_manager.delegate_task("engineer", "Fix a ZeroDivisionError in test_script.py: ```python\ndef divide(a, b):\n    return a / b  # Fails on b=0\n```")
    print(f"✅ Agent Response:\n{response}")