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
            "reviewer": "deepseek-r1-distill-qwen-7b",  # DeepSeek Qwen 7B for faster review (adjust later if needed)
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

    def send_task(self, agent, task_prompt, timeout=300):  # Maintained for stability
        model = self.agents.get(agent, "codestral-22b-v0.1")  # Ensure only Codestral/DeepSeek/Llama
        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": task_prompt}],  # Plain prompt, no <s>[INST] ... [/INST]</s>
                    "max_tokens": 1024,  # Ensure full function
                    "temperature": 0.05,  # Slight flexibility for code output
                    "stop": ["```", "\n"]  # Stop at code blocks or newlines for better control
                },
                timeout=timeout
            )
            response.raise_for_status()
            response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            if not response_text:
                return f"❌ Empty response from {agent} ({model})."
            print(f"Raw response from {agent} ({model}): {response_text}")  # Debug logging
        except requests.exceptions.Timeout:
            return f"❌ Timeout: {agent} ({model}) did not respond in {timeout} seconds."
        except requests.exceptions.RequestException as e:
            return f"❌ API Error: {agent} ({model}) - {e}"
        return response_text

    def review_task(self, codestral_output, timeout=300):
        """Review and clean Codestral's output using DeepSeek Qwen 7B for faster, lighter review."""
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
        """Extracts Python function—accepts code blocks, ensures complete try/except for specific errors, caps retries."""
        if self.retry_count >= self.max_retries:
            print(f"⚠️ Max retries reached for this task. Using fallback.")
            return "def placeholder():\n    pass"
        
        # Allow code blocks, reject standalone prose, <think> blocks, or test cases
        if not ai_response or ai_response.startswith("❌") or ai_response == "ERROR: No valid function found.":
            print(f"⚠️ Preprocessing failed: Empty, error, or invalid response detected in:\n{ai_response}")
            self.retry_count += 1
            return None
        
        # Look for code block directly
        code_block = re.search(r"```python\s*(.*?)\s*```", ai_response, re.DOTALL)
        if code_block:
            code = code_block.group(1).strip()
        else:
            # Fallback: look for raw function with try/except for specific errors, ignoring prose/<think>
            prose_or_think = re.search(r"(?:Here's|Here is|<think>).*?(def\s+\w+$$ .*? $$:.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None))", ai_response, re.DOTALL | re.IGNORECASE)
            if prose_or_think:
                code = prose_or_think.group(1).strip()
            else:
                raw_func = re.search(r"(def\s+\w+$$ .*? $$:.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None))", ai_response, re.DOTALL | re.MULTILINE)
                if raw_func:
                    code = raw_func.group(1).strip()
                else:
                    print(f"⚠️ Preprocessing failed: No valid function in:\n{ai_response}")
                    self.retry_count += 1
                    return None

        # Validate complete try/except for specific errors, reject test cases, <think>, or generic except
        if ("try:" in code and "except" in code and "return None" in code and 
            any(error in code for error in ["ZeroDivisionError", "KeyError"]) and 
            not any(prose in code.lower() for prose in ["test case", "simulated", "<think>"]) and 
            "except:" not in code):  # Reject generic except clauses
            self.retry_count = 0  # Reset on success
            return code
        print(f"⚠️ Preprocessing warning: Incomplete, invalid, or generic function in:\n{code}")
        self.retry_count += 1
        return None

    def delegate_task(self, agent, task_description, save_to=None, timeout=300):
        print(f"🔹 Sending task to {agent}: {task_description} (Timeout: {timeout}s)")
        # Extract error and script content from task_description, handle missing or malformed delimiters
        try:
            error = task_description.split(" in ")[0]
            script_part = task_description.split(" in ")[1]
            script_name = script_part.split(":")[0]
            # Try multiple delimiter patterns to handle variations
            if "```python\n" in script_part and "```" in script_part:
                script_content = script_part.split("```python\n")[1].split("```")[0]
            elif ": ```python\n" in task_description and "```" in task_description:
                script_content = task_description.split(": ```python\n")[1].split("```")[0]
            else:
                script_content = script_part.split(": ")[1] if ": " in script_part else script_part
        except (IndexError, AttributeError) as e:
            print(f"⚠️ Error parsing task description: {e}. Using raw task description as script content.")
            error = task_description.split(" in ")[0] if " in " in task_description else "UnknownError"
            script_content = task_description.split(": ```python\n")[1].split("```")[0] if ": ```python\n" in task_description and "```" in task_description else task_description

        result = self.send_task(
            agent,
            f"Please debug the following script and return ONLY the COMPLETE fixed function in Python using a FULL try/except block with the appropriate except clause to handle the error ({error}), returning None, with NO extra logic, NO prose, and NO explanations, inside ```python ... ```.",
            timeout
        )
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌") or result == "ERROR: No valid function found.":
            print(f"❌ AI response invalid, empty, or error for {agent}. Retrying with adjusted prompt...")
            result = self.send_task(
                agent,
                f"Please debug the following script and return ONLY the COMPLETE fixed function in Python using a FULL try/except block with the appropriate except clause to handle {error}, returning None, with NO extra logic, NO prose, and NO explanations, inside ```python ... ```.",
                timeout + 60
            )
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌") or result == "ERROR: No valid function found.":
            print("❌ Still invalid, empty, or error. One last try with strict mode...")
            result = self.send_task(
                agent,
                f"STRICT MODE: Please debug the following script and return ONLY the COMPLETE fixed function in Python using a FULL try/except block with the appropriate except clause to handle {error}, returning None, with NO extra logic, NO prose, and NO explanations, inside ```python ... ```. Respond with code or 'ERROR: No response.'",
                timeout + 60
            )
        
        if not isinstance(result, str) or result.strip() == "" or result.startswith("❌") or result == "ERROR: No response.":
            print("❌ Still invalid, empty, or error. Using fallback after max retries.")
            self.retry_count = 0  # Reset for next task
            return "def placeholder():\n    pass"
        
        # Review the response if it contains prose, <think>, or needs cleaning
        if any(prose in result.lower() for prose in ["here's", "here is", "corrected", "fixed", "modified", "<think>"]):
            reviewed_fix = self.review_task(result, timeout)
            if reviewed_fix and isinstance(reviewed_fix, str) and reviewed_fix.strip() and reviewed_fix != "ERROR: No valid function found.":
                if "```python" in reviewed_fix:
                    try:
                        fix = re.search(r"```python\s*(.*?)\s*```", reviewed_fix, re.DOTALL).group(1).strip()
                    except AttributeError:
                        print(f"⚠️ Reviewed fix not in ```python``` format—using original response.")
                        fix = result
                elif re.search(r"(def\s+\w+\(.*?\):.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None))", reviewed_fix, re.DOTALL | re.MULTILINE):
                    # Extract raw try/except function with specific errors if ```python``` is missing
                    fix = re.search(r"(def\s+\w+\(.*?\):.*?(try:.*?except\s+(?:ZeroDivisionError|KeyError):.*?return\s+None))", reviewed_fix, re.DOTALL | re.MULTILINE).group(1).strip()
                else:
                    print(f"⚠️ Reviewed fix missing valid ```python``` or specific try/except—using original response.")
                    fix = result
            else:
                print(f"❌ Review failed or empty—using original response.")
                fix = result
        else:
            fix = result

        final_fix = self.preprocess_ai_response(fix)
        if final_fix is None:
            print("❌ Preprocessing failed after review. Using fallback.")
            self.retry_count = 0  # Reset for next task
            return "def placeholder():\n    pass"
        
        self.retry_count = 0  # Reset on success
        return final_fix

if __name__ == "__main__":
    agent_manager = AgentManager()
    response = agent_manager.delegate_task("engineer", "Fix a ZeroDivisionError in test_script.py: ```python\ndef divide(a, b):\n    return a / b  # Fails on b=0\n```")
    print(f"✅ Agent Response:\n{response}")