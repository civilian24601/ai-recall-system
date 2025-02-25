# /mnt/f/projects/ai-recall-system/code_base/agent_manager.py

import requests
import re
import os
from code_base.network_utils import detect_api_url  # <-- NEW IMPORT

class AgentManager:
    """Manages AI Agents for architecture, coding, review, and automation."""

    def __init__(self):
        """Initialize agents and set API URL."""
        self.agents = {
            "architect": "deepseek-coder-33b-instruct",
            "engineer": "deepseek-coder-33b-instruct",
            "reviewer": "meta-llama-3-8b-instruct",
            "qa": "deepseek-coder-33b-instruct",
            "devops": "deepseek-r1-distill-qwen-7b",
            "oversight": "deepseek-r1-distill-qwen-7b",
            "feedback": "deepseek-coder-33b-instruct",
            "preprocessor": "deepseek-coder-v2-lite-instruct"
        }

        # Use our shared utility to detect environment & set LM Studio endpoint
        self.api_url = detect_api_url()
        self.code_dir = "/mnt/f/projects/ai-recall-system/code_base/agents/"

    def send_task(self, agent, task_prompt, timeout=180):
        """
        Sends a task to an AI agent for execution with timeout handling.
        
        Args:
            agent (str): The agent key identifying which model to use.
            task_prompt (str): The prompt or instructions for the agent.
            timeout (int): Time in seconds to wait for a response.

        Returns:
            str: The text response from the AI or error message.
        """
        model = self.agents.get(agent, "deepseek-coder-33b-instruct")

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": task_prompt}],
                    "max_tokens": 800,
                    "temperature": 0.7
                },
                timeout=timeout
            )
            response.raise_for_status()
            response_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        except requests.exceptions.Timeout:
            response_text = f"❌ Timeout: {agent} did not respond in {timeout} seconds."
        except requests.exceptions.RequestException as e:
            response_text = f"❌ API Error: {e}"

        return response_text

    def preprocess_ai_response(self, ai_response):
        """
        Uses a small LLM to preprocess AI responses before extracting Python code blocks.
        
        Args:
            ai_response (str): The raw text from the main AI agent.

        Returns:
            str: A cleaned Python function (as a string).
        """
        return self.send_task(
            "preprocessor",
            (
                "Reformat the following text into a clean Python function:\n\n"
                f"{ai_response}\n\n"
                "Ensure that the response only contains a valid Python function "
                "with NO explanations or markdown artifacts."
            ),
            timeout=30  # Quick response needed
        )

    def delegate_task(self, agent, task_description, save_to=None, timeout=60):
        """
        Delegates tasks to the appropriate AI agent and ensures valid responses.

        Args:
            agent (str): The agent key for the desired model (e.g. 'engineer').
            task_description (str): The instructions for the agent.
            save_to (str, optional): If provided, indicates where to save the result.
            timeout (int): How many seconds to wait for a reply.

        Returns:
            str: The AI agent's response, guaranteed to be non-empty code.
        """
        print(f"🔹 Sending task to {agent}: {task_description} (Timeout: {timeout}s)")

        result = self.send_task(agent, task_description, timeout)

        # Ensure AI response is always a string
        if not isinstance(result, str) or result.strip() == "":
            print("❌ AI response is not a valid string. Retrying with stricter formatting request...")
            result = self.send_task(
                agent,
                (
                    f"STRICT MODE: {task_description}. Your response MUST be a single function "
                    "inside triple backticks (```python ... ```). NO explanations, ONLY code."
                ),
                timeout + 60
            )

        # If AI still fails, provide a default suggestion
        if not isinstance(result, str) or result.strip() == "":
            print("❌ AI response is still invalid after retry. Using generic fallback fix.")
            result = "```python\ndef placeholder_function():\n    pass\n```"

        # Optionally, we could store or log the final result here
        # e.g., store in blueprint execution logs or debug logs

        return result

# 🚀 Example Usage
if __name__ == "__main__":
    agent_manager = AgentManager()
    response = agent_manager.delegate_task("engineer", "Fix a ZeroDivisionError in a test script.")
    print(f"✅ Agent Response:\n{response}")
