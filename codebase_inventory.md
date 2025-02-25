
# 📂 code_base/agent_manager.py

# /mnt/f/projects/ai-recall-system/code_base/agent_manager.py

import requests
import re
import os
from network_utils import detect_api_url  # <-- NEW IMPORT

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

---

# 📂 code_base/api_structure.py

# /mnt/f/projects/ai-recall-system/code_base/api_structure.py

import requests
from flask import Flask, request
from flask_restful import Resource, Api
from network_utils import detect_api_url  # <-- Now we can import the same logic if we want

app = Flask(__name__)
api = Api(app)

class APIHandler(Resource):
    """Handles API requests and connects to AI processing."""

    def post(self):
        """
        Process user input and send it to the local LM Studio for a response.

        Expected JSON Input:
        {
            "prompt": "User prompt here..."
        }
        """
        data = request.get_json()
        user_prompt = data.get("prompt", "")

        deepseek_response = self.query_deepseek(user_prompt)
        return {"status": "success", "response": deepseek_response}

    def query_deepseek(self, prompt):
        """
        Send user input to LM Studio using the same environment detection as agent_manager.

        Args:
            prompt (str): The user query or instruction.

        Returns:
            str: AI response text or an error message.
        """
        # Use the unified environment detection
        api_url = detect_api_url(default_url="http://10.5.0.2:1234/v1/chat/completions")
        # If you prefer the user to set that IP, you could pass it as a param or use an env var

        try:
            response = requests.post(
                api_url,
                json={
                    "model": "deepseek-coder-33b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error {response.status_code}: AI response not available."
        except requests.exceptions.RequestException as e:
            return f"Error communicating with LM Studio: {e}"

api.add_resource(APIHandler, "/api/task")

if __name__ == "__main__":
    # This is typically used for manual testing or for a separate QA flow
    # in case you want to expose a simple Flask endpoint to test the local model
    app.run(debug=True, host="0.0.0.0", port=5000)

---

# 📂 code_base/core_architecture.py

import os
import requests
import json

class CoreArchitecture:
    """Handles AI pipeline initialization & self-improvement management."""

    def __init__(self):
        self.configurations = {}

    def initialize_pipeline(self):
        """Handles AI pipeline initialization."""
        print("✅ AI Pipeline Initialized.")

    def manage_improving_modules(self):
        """Manages self-improving modules."""
        print("✅ Self-Improving Modules Managed.")

    def load_store_ai_configurations(self):
        """Loads and stores AI configurations."""
        self.configurations = {"version": "1.0", "status": "active"}
        print(f"✅ Configurations Loaded: {self.configurations}")


class AIManager:
    """Manages AI queries, including knowledge base lookups and LLM inference."""

    def __init__(self, knowledge_base_path):
        """Initializes AI Manager & loads knowledge base."""
        self.knowledge_base_path = knowledge_base_path
        self.knowledge_base = {}
        self.llm_api = self.detect_llm_api()  # Dynamically detect best LLM API
        self.load_knowledge_base()

    def detect_llm_api(self):
        """Detects if LM Studio API is accessible."""
        test_urls = [
            "http://localhost:1234/v1/chat/completions",
            "http://host.docker.internal:1234/v1/chat/completions"
        ]
        for url in test_urls:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    print(f"✅ Using LLM API at: {url}")
                    return url
            except requests.ConnectionError:
                continue
        raise RuntimeError("❌ LLM API is unreachable. Start LM Studio!")

    def load_knowledge_base(self):
        """Loads markdown knowledge into memory."""
        knowledge_files = [f for f in os.listdir(self.knowledge_base_path) if f.endswith(".md")]

        for file in knowledge_files:
            file_path = os.path.join(self.knowledge_base_path, file)
            with open(file_path, "r", encoding="utf-8") as f:
                self.knowledge_base[file] = f.read()
        
        print(f"✅ Loaded {len(self.knowledge_base)} knowledge files into memory.")

    def query_knowledge_base(self, query):
        """Improves knowledge retrieval by prioritizing exact filename matches & extending output length."""
        query_lower = query.lower().strip()
        
        # 🔍 Step 1: Check for exact filename match
        if query_lower.endswith(".md") and query_lower in self.knowledge_base:
            content = self.knowledge_base[query_lower]
            return f"📄 Exact match found in {query_lower}:\n\n{content[:1000]}..."  # Extend snippet length
        
        # 🔍 Step 2: Search for best content match
        best_match = None
        best_score = 0
        for file, content in self.knowledge_base.items():
            if query_lower in file.lower():  # Prioritize filenames first
                return f"📄 Matched filename: {file}:\n\n{content[:1000]}..."
            
            score = self._calculate_match_score(query_lower, content)
            if score > best_score:
                best_score = score
                best_match = f"🔍 Best match in {file}:\n\n{content[:1000]}..."

        return best_match or "🤖 No relevant knowledge found."

    def _calculate_match_score(self, query, content):
        """Basic similarity scoring to find the most relevant knowledge base entry."""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        return len(query_words & content_words) / max(len(query_words), 1)


    def query_deepseek(self, prompt):
        """Calls DeepSeek AI model when knowledge base lacks an answer."""
        response = requests.post(
            self.llm_api,
            json={
                "model": "deepseek-coder-33b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.7
            }
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return "Error: AI response not available."

    def process_query(self, query):
        """Checks knowledge base first, then calls DeepSeek if needed."""
        kb_response = self.query_knowledge_base(query)
        if kb_response and "🤖 No relevant knowledge found." not in kb_response:
            return kb_response

        print("📡 No match in knowledge base, querying DeepSeek...")
        return self.query_deepseek(query)


# Example Usage
if __name__ == "__main__":
    core = CoreArchitecture()
    core.initialize_pipeline()
    core.manage_improving_modules()
    core.load_store_ai_configurations()

    ai_manager = AIManager("/mnt/f/projects/ai-recall-system/knowledge_base")
    print(ai_manager.process_query("project_overview.md"))  # Example query

---

# 📂 code_base/debugging_strategy.py

import json
import datetime

class DebuggingStrategy:
    """Manages AI debugging strategies and tracks effectiveness."""

    def __init__(self):
        self.strategy_log_file = "../logs/debugging_strategy_log.json"
        self.debug_logs_file = "../logs/debug_logs.json"

    def load_strategy_logs(self):
        """Loads past debugging strategies from log file."""
        try:
            with open(self.strategy_log_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []  # Return empty if file is missing or corrupted

    def save_strategy_logs(self, strategies):
        """Saves updated debugging strategies to log file."""
        with open(self.strategy_log_file, "w") as f:
            json.dump(strategies, f, indent=4)

    def get_debugging_strategy(self, error_type):
        """Returns a debugging strategy based on historical data."""
        strategies = self.load_strategy_logs()

        # Find a past debugging strategy for this error type
        matching_strategies = [s for s in strategies if s["error_type"] == error_type]
        
        if matching_strategies:
            # Sort by success rate and return the best strategy
            best_strategy = sorted(matching_strategies, key=lambda x: x["success_rate"], reverse=True)[0]
            return best_strategy["strategy"]
        
        # Default strategy if no past strategy exists
        return "Standard debugging: AI will analyze logs, suggest fixes, and request verification."

    def update_strategy(self, error_type, strategy, success):
        """Updates debugging strategy based on results."""
        strategies = self.load_strategy_logs()

        # Check if this strategy exists
        for entry in strategies:
            if entry["error_type"] == error_type and entry["strategy"] == strategy:
                # Update success rate
                entry["attempts"] += 1
                if success:
                    entry["successful_fixes"] += 1
                entry["success_rate"] = entry["successful_fixes"] / entry["attempts"]
                self.save_strategy_logs(strategies)
                return
        
        # Add a new strategy if it doesn't exist
        strategies.append({
            "error_type": error_type,
            "strategy": strategy,
            "attempts": 1,
            "successful_fixes": 1 if success else 0,
            "success_rate": 1.0 if success else 0.0
        })

        self.save_strategy_logs(strategies)

    def analyze_previous_fixes(self):
        """Analyzes past fixes to identify patterns and improve strategies."""
        try:
            with open(self.debug_logs_file, "r") as f:
                debug_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return

        for entry in debug_logs:
            # Only process logs that contain an "error" field
            if "error" in entry and "fix_attempted" in entry:
                print(f"🔍 Processing error log: {entry['error']}")  # Debugging print
                self.update_strategy(entry["error"], entry["fix_attempted"], success=True)

# 🚀 Example Usage
if __name__ == "__main__":
    debugger = DebuggingStrategy()
    debugger.analyze_previous_fixes()
    
    # Example: Get a debugging strategy for a new error type
    strategy = debugger.get_debugging_strategy("ZeroDivisionError: division by zero")
    print(f"Recommended Debugging Strategy: {strategy}")

---

# 📂 code_base/generate_knowledge_base.py

import os

# 🔹 Knowledge base directory
BASE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases"

# 🔹 Predefined knowledge content for each agent
KNOWLEDGE_CONTENT = {
    "architect_knowledge": """# AI System Architecture Principles

## 1. Modular Design
- Split the system into independent modules that communicate via APIs.
- Each module should have a clear **responsibility** (e.g., data handling, ML models, UI).

## 2. Scalability
- Implement **horizontal scaling** where possible.
- Use **containerization (Docker/Kubernetes)** for deployment.

## 3. Versioning & Documentation
- Maintain a versioning system for architecture changes.
- Document all API interactions and agent workflows.

""",
    "engineer_knowledge": """# Software Engineering & API Best Practices

## 1. Clean Code
- Use **descriptive variable names** and **modular functions**.
- Follow **PEP8** for Python development.

## 2. API Development
- Use **Flask/FastAPI** for lightweight API services.
- Implement **rate limiting & authentication** for security.

## 3. Error Handling
- Use **try-except** blocks to prevent crashes.
- Log all **critical errors** for debugging.

""",
    "reviewer_knowledge": """# Code Review Best Practices

## 1. Code Readability
- Ensure consistent **code formatting** (Black, Flake8).
- Minimize **nested loops** and **complex logic**.

## 2. Security & Performance
- Validate **API inputs** against SQL injection and XSS attacks.
- Optimize **database queries** for speed.

""",
    "qa_knowledge": """# AI & Software Testing Strategies

## 1. Unit Testing
- Use **pytest** for automated unit tests.
- Test all **critical functions** before deployment.

## 2. Integration Testing
- Simulate real-world **user interactions**.
- Validate **API response consistency**.

## 3. Edge Case Handling
- Test for **invalid inputs**, **missing fields**, and **high loads**.

""",
    "devops_knowledge": """# DevOps & CI/CD Best Practices

## 1. Deployment Pipeline
- Use **GitHub Actions/Jenkins** for CI/CD.
- Automate **container builds** and **server deployments**.

## 2. Infrastructure as Code
- Use **Terraform** or **Ansible** to manage infrastructure.
- Avoid **manual server configuration**.

## 3. Monitoring & Logging
- Implement **Prometheus/Grafana** for real-time monitoring.
- Store logs using **ELK stack**.

""",
    "oversight_knowledge": """# AI Oversight & Compliance

## 1. Ethical AI Development
- Ensure **AI decisions are explainable** and **bias-free**.
- Comply with **GDPR** and **AI safety standards**.

## 2. Security Audits
- Regularly scan for **vulnerabilities in dependencies**.
- Use **role-based access control (RBAC)**.

## 3. System Integrity Checks
- Automate security scans for **code changes**.
- Require **human validation for major updates**.

""",
    "feedback_knowledge": """# AI Feedback & Continuous Learning

## 1. User Feedback Handling
- Log all **user complaints & feature requests**.
- Auto-categorize feedback by **priority & impact**.

## 2. AI Model Evaluation
- Monitor **LLM performance & hallucination rates**.
- Retrain AI models based on **real-world data**.

""",
}


def create_knowledge_bases():
    """Creates knowledge base directories & populates them with markdown content."""
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    for folder, content in KNOWLEDGE_CONTENT.items():
        folder_path = os.path.join(BASE_DIR, folder)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, "README.md")
        with open(file_path, "w") as f:
            f.write(content)

        print(f"✅ Generated {file_path}")


if __name__ == "__main__":
    create_knowledge_bases()
    print("🎉 All agent knowledge bases have been created and populated!")

---

# 📂 code_base/generate_project_summary.py

import os
import json

# Define project root and output file
PROJECT_ROOT = "/mnt/f/projects/ai-recall-system/"
OUTPUT_FILE = "/mnt/f/projects/ai-recall-system/logs/project_summary.md"

# File types to include
INCLUDE_EXTENSIONS = {".py", ".md", ".json", ".yml", ".toml"}

def get_file_summary(file_path):
    """Extracts content from the file and summarizes it."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if file_path.endswith(".py"):
                content = "".join(lines[:30])  # Grab first 30 lines for context
            else:
                content = "".join(lines[:50])  # Longer context for docs
        return content.strip()
    except Exception as e:
        return f"Error reading file: {e}"

def generate_project_summary():
    """Generates a markdown summary of the entire project structure with key content."""
    summary = ["# AI Recall System - Project Summary\n"]
    
    # Walk through project directory
    for root, _, files in os.walk(PROJECT_ROOT):
        for file in files:
            file_ext = os.path.splitext(file)[1]
            if file_ext in INCLUDE_EXTENSIONS:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, PROJECT_ROOT)
                
                # Format output
                summary.append(f"## {relative_path}")
                summary.append(f"**File:** `{file}`")
                summary.append(f"**Path:** `{relative_path}`\n")
                summary.append("### Summary:\n")
                summary.append("```" + file_ext[1:] + "\n" + get_file_summary(file_path) + "\n```")
                summary.append("\n---\n")

    # Save summary to markdown
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(summary))

    print(f"✅ Project summary saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_project_summary()

---

# 📂 code_base/generate_work_summary.py

import chromadb
import datetime
import json
import requests

class WorkSummaryGenerator:
    """Generates daily AI summaries based on work session logs."""

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        self.collection = self.chroma_client.get_or_create_collection(name="work_sessions")
        self.api_url = self.detect_api_url()  # Ensure AI API detection works
        self.summary_md_file = "../logs/daily_summary.md"
        self.summary_json_file = "../logs/daily_summary.json"

    def detect_api_url(self):
        """Detect the correct API URL based on whether we are in WSL or native Windows."""
        wsl_ip = "172.17.128.1"
        default_url = "http://localhost:1234/v1/chat/completions"

        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    print(f"🔹 Detected WSL! Using Windows IP: {wsl_ip}")
                    return f"http://{wsl_ip}:1234/v1/chat/completions"
        except FileNotFoundError:
            pass

        print(f"🔹 Using default API URL: {default_url}")
        return default_url

    def retrieve_work_sessions(self, hours=24):
        """Retrieves work session logs from the past `hours` from ChromaDB."""
        results = self.collection.get(limit=100)

        if not results or "documents" not in results:
            return []

        # Convert stored JSON strings into dictionaries
        session_logs = []
        for doc in results["documents"]:
            try:
                parsed_doc = json.loads(doc)
                # Ensure each log has a timestamp, otherwise default to "Unknown"
                parsed_doc["timestamp"] = parsed_doc.get("timestamp", "Unknown")
                session_logs.append(parsed_doc)
            except json.JSONDecodeError:
                print(f"❌ Skipping malformed entry: {repr(doc)}")

        # Filter logs from the last `hours`
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        recent_sessions = [
            log for log in session_logs
            if log["timestamp"] != "Unknown" and datetime.datetime.strptime(log["timestamp"], "%Y-%m-%d %H:%M:%S") >= cutoff_time
        ]

        return recent_sessions

    def generate_summary(self):
        """Uses DeepSeek Coder 33B to summarize past work sessions."""
        recent_sessions = self.retrieve_work_sessions(hours=24)
        if not recent_sessions:
            return "⚠ No recent work sessions available for summarization."

        work_log_text = "\n".join([json.dumps(session, indent=2) for session in recent_sessions])

        prompt = (
            "Analyze the following AI work sessions and summarize the key tasks completed, "
            "problems encountered, and unresolved issues. Generate a structured and concise summary.\n\n"
            f"Work Session Logs:\n{work_log_text}"
        )

        try:
            response = requests.post(
                self.api_url,
                json={
                    "model": "deepseek-coder-33b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            summary_text = response.json().get("choices", [{}])[0].get("message", {}).get("content", "Error generating summary.")

            self.store_summary(summary_text)
            return summary_text

        except requests.exceptions.RequestException as e:
            return f"❌ API Error: {e}"

    def store_summary(self, summary_text):
        """Stores AI-generated summaries in both Markdown and JSON formats."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save Markdown Summary
        markdown_entry = f"## [{timestamp}] AI Work Summary\n{summary_text}\n"
        with open(self.summary_md_file, "a") as f:
            f.write(markdown_entry + "\n")

        # Save JSON Summary
        summary_data = {"timestamp": timestamp, "summary": summary_text}
        with open(self.summary_json_file, "w") as f:
            json.dump(summary_data, f, indent=2)

        print(f"✅ Work summary stored successfully at {timestamp}")

if __name__ == "__main__":
    generator = WorkSummaryGenerator()
    summary = generator.generate_summary()
    print("\n🔍 AI-Generated Daily Work Summary:\n", summary)

---

# 📂 code_base/map_project_structure.py

import os
import json
from datetime import datetime

PROJECT_ROOT = "/mnt/f/projects/ai-recall-system"
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "logs/project_structure.json")


def map_directory(root_dir):
    """Recursively maps the entire project directory."""
    project_map = {}
    for root, dirs, files in os.walk(root_dir):
        relative_path = os.path.relpath(root, PROJECT_ROOT)
        project_map[relative_path] = {"dirs": dirs, "files": files}
    return project_map


def save_structure():
    """Saves the mapped project directory to a JSON file."""
    project_structure = {
        "timestamp": datetime.now().isoformat(),
        "structure": map_directory(PROJECT_ROOT),
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(project_structure, f, indent=4)
    print(f"✅ Project directory structure saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    save_structure()

---

# 📂 code_base/multi_agent_workflow.py

import time
import sys
import json
import datetime
import re
import os
from agent_manager import AgentManager

class SingleAgentWorkflow:
    """Executes AI recall, debugging, and code retrieval workflows in single-agent mode."""

    def __init__(self):
        self.agent_manager = AgentManager()
        self.debug_log_file = "../logs/debug_logs.json"
        self.test_scripts_dir = "./test_scripts/"
        self.ai_timeout = 300

    def generate_log_id(self, prefix="log"):
        """Generates a unique ID for debugging log entries."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}"

    def retrieve_past_debug_logs(self):
        """Retrieve past debugging logs from local storage."""
        print("🔍 Retrieving past debugging logs...")
        try:
            with open(self.debug_log_file, "r") as f:
                logs = json.load(f)
                if not logs:
                    print("⚠ No debugging logs found.")
                    return []
                print(f"✅ Retrieved {len(logs)} logs.")
                return logs
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Debugging log file missing or corrupted. Error: {e}")
            return []

    def run_workflow(self):
        """Executes a structured AI debugging & recall workflow for ALL pending issues."""
        print("\n🚀 Starting Single-Agent AI Workflow...\n")

        past_debug_logs = self.retrieve_past_debug_logs()
        if not past_debug_logs:
            print("❌ No past debugging logs available.")
            return

        print(f"🔍 Checking for unresolved debugging issues...")
        unresolved_logs = [
            log for log in past_debug_logs 
            if log.get("resolved") is False and "stack_trace" in log
        ]

        if not unresolved_logs:
            print("✅ No unresolved debugging issues found.")
            return

        print(f"🔍 Found {len(unresolved_logs)} unresolved logs to process.")

        for error_entry in unresolved_logs:
            script_name = error_entry.get("stack_trace", "").split("'")[1] if "stack_trace" in error_entry else None
            if not script_name:
                print(f"⚠ Skipping log entry with missing `stack_trace`: {error_entry}")
                continue

            print(f"🔹 AI will attempt to fix `{script_name}` based on debugging logs.")

            script_path = os.path.join(self.test_scripts_dir, script_name)
            script_content = ""
            if os.path.exists(script_path):
                with open(script_path, "r") as f:
                    script_content = f.read()

            if not script_content.strip():
                print(f"⚠ `{script_name}` is empty or unavailable. Skipping AI fix.")
                continue

            print("🔹 AI Analyzing Debugging Logs...")
            ai_fix_suggestion = self.agent_manager.delegate_task(
                "debug",
                f"Analyze `{script_name}` and find the source of the following error: {error_entry['error']}. "
                "Read the script below and determine how to correctly fix it."
                "Your response MUST ONLY contain the corrected function inside triple backticks (```python ... ```), NO explanations."
                "\nHere is the current content of `{script_name}`:\n"
                "```python\n"
                f"{script_content}\n"
                "```",
                timeout=self.ai_timeout
            )

            extracted_fix = self.agent_manager.preprocess_ai_response(ai_fix_suggestion)

            print(f"✅ AI Suggested Fix:\n{extracted_fix}\n")
            confirmation = input("Did the fix work? (y/n): ").strip().lower()
            fix_verified = confirmation == "y"

            error_entry["fix_attempted"] = extracted_fix
            error_entry["resolved"] = fix_verified
            error_entry["fix_successful"] = fix_verified

            try:
                with open(self.debug_log_file, "r") as f:
                    logs = json.load(f)

                for i, entry in enumerate(logs):
                    if entry["id"] == error_entry["id"]:
                        logs[i] = error_entry  # Update existing log entry

                with open(self.debug_log_file, "w") as f:
                    json.dump(logs, f, indent=4)

                print("✅ Debugging log successfully updated in `debug_logs.json`.")

            except Exception as e:
                print(f"❌ Failed to update debugging log: {e}")

        print("\n✅ Single-Agent AI Workflow Completed!\n")

# 🚀 Example Usage
if __name__ == "__main__":
    workflow = SingleAgentWorkflow()
    workflow.run_workflow()

---

# 📂 code_base/network_utils.py

# /mnt/f/projects/ai-recall-system/code_base/network_utils.py

import os

def detect_api_url(default_url="http://localhost:1234/v1/chat/completions", wsl_ip="172.17.128.1"):
    """
    Detect the correct API URL based on whether we are in WSL or native Windows.

    Args:
        default_url (str): The default local LM Studio URL to use if not in WSL.
        wsl_ip (str): The IP address to use if WSL is detected.

    Returns:
        str: The appropriate URL for LM Studio requests.
    """
    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                print(f"🔹 Detected WSL! Using Windows IP: {wsl_ip}")
                return f"http://{wsl_ip}:1234/v1/chat/completions"
    except FileNotFoundError:
        pass

    print(f"🔹 Using default API URL: {default_url}")
    return default_url

---

# 📂 code_base/store_markdown_in_chroma.py

import chromadb
import os

def store_markdown_in_chroma():
    """Indexes refined markdown logs into ChromaDB for AI recall."""
    chroma_client = chromadb.PersistentClient(path="chroma_db/")
    collection = chroma_client.get_or_create_collection("markdown_logs")

    log_dirs = ["logs/", "knowledge_base/"]
    for log_dir in log_dirs:
        for filename in os.listdir(log_dir):
            if filename.endswith(".md"):
                with open(os.path.join(log_dir, filename), "r") as f:
                    text_content = f.read()
                    collection.add(
                        documents=[text_content],
                        metadatas=[{"filename": filename}],
                        ids=[filename]
                    )

    print(f"✅ All markdown logs indexed in ChromaDB!")

# Example usage
store_markdown_in_chroma()

---

# 📂 code_base/user_interaction_flow.py

import requests
import json
import os
from core_architecture import AIManager

class UserInteractionCLI:
    """Handles user interaction via CLI."""

    def __init__(self):
        self.url = self.detect_api_url()
        self.ai_manager = AIManager("/mnt/f/projects/ai-recall-system/knowledge_base")

    def detect_api_url(self):
        """Detects if Flask API is accessible using a test POST request."""
        test_urls = [
            "http://localhost:5000/api/task",
            "http://host.docker.internal:5000/api/task"
        ]
        test_payload = {"prompt": "test"}

        for url in test_urls:
            try:
                response = requests.post(url, json=test_payload)
                if response.status_code == 200:
                    print(f"✅ Using Flask API at: {url}")
                    return url
            except requests.ConnectionError:
                continue

        raise RuntimeError("❌ Flask API is unreachable. Start `api_structure.py`!")

    def get_user_input(self) -> str:
        """Captures user input from the command line."""
        return input("Please enter your query: ")

    def send_to_API(self, prompt: str):
        """Sends input to AI API, preferring knowledge base results first."""
        kb_response = self.ai_manager.process_query(prompt)

        if "🤖 No relevant knowledge found." not in kb_response:
            return kb_response  # ✅ Return knowledge base result if found

        print("📡 No match in knowledge base, querying AI API...")

        headers = {"Content-Type": "application/json"}
        data = json.dumps({"prompt": prompt})
        response = requests.post(self.url, headers=headers, data=data)

        if response.status_code == 200:
            return response.json()["response"]
        return "Error: API request failed."

    def display_to_user(self, ai_output):
        """Displays AI responses with proper formatting & prevents truncation."""
        print("\n🔹 AI Response:\n")
        print(ai_output)
        print("\n" + "=" * 80)  # Separator for readability



class UserInteractionManager:
    """Handles structured interactions and logs them for future training."""

    def __init__(self, log_path="/mnt/f/projects/ai-recall-system/chatgpt_dumps/interactions.json"):
        self.interactions = []
        self.cli = UserInteractionCLI()
        self.log_path = log_path
        self.load_existing_interactions()

    def load_existing_interactions(self):
        """Loads past interactions from log file."""
        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                self.interactions = json.load(f)
            print(f"✅ Loaded {len(self.interactions)} past interactions.")

    def handle_interaction(self):
        """Structures the interaction flow."""
        prompt = self.cli.get_user_input()
        response = self.cli.send_to_API(prompt)
        self.log_interaction(prompt, response)
        self.cli.display_to_user(response)

    def log_interaction(self, prompt: str, response: dict):
        """Logs interactions & triggers AI self-improvement."""
        interaction = {"query": prompt, "response": response}
        self.interactions.append(interaction)

        # ✅ Automatically save interactions
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.interactions, f, indent=4)

        print("🔄 AI is analyzing past queries to refine knowledge...")

# Example Usage
if __name__ == "__main__":
    manager = UserInteractionManager()
    manager.handle_interaction()

---

# 📂 code_base/work_session_logger.py

import datetime
import json
import chromadb
import traceback
import time

class WorkSessionLogger:
    """Handles AI work session logging, retrieval, and structured summaries."""

    def __init__(self):
        self.session_log_file = "../logs/work_session.md"
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        self.collection = self.chroma_client.get_or_create_collection(name="work_sessions")
        self.api_url = self.detect_api_url()  # Automatically detect correct API URL

    def detect_api_url(self):
        """Detect the correct API URL based on whether we are in WSL or native Windows."""
        wsl_ip = "172.17.128.1"
        default_url = "http://localhost:1234/v1/chat/completions"

        try:
            with open("/proc/version", "r") as f:
                if "microsoft" in f.read().lower():
                    print(f"🔹 Detected WSL! Using Windows IP: {wsl_ip}")
                    return f"http://{wsl_ip}:1234/v1/chat/completions"
        except FileNotFoundError:
            pass

        print(f"🔹 Using default API URL: {default_url}")
        return default_url

    def log_work_session(self, task, files_changed=None, error_details=None, execution_time=None, outcome=None):
        """Logs a structured work session entry."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = {
            "timestamp": timestamp,
            "task": task,
            "files_changed": files_changed or [],
            "error_details": error_details or "None",
            "execution_time": f"{execution_time:.2f}s" if execution_time else "N/A",
            "outcome": outcome or "N/A"
        }

        # Store log in ChromaDB
        self.collection.add(ids=[timestamp], documents=[json.dumps(log_entry)])

        # Format for Markdown
        markdown_entry = f"## [{timestamp}] {task}\n"
        markdown_entry += f"- **Files Changed:** {', '.join(log_entry['files_changed'])}\n"
        markdown_entry += f"- **Errors Encountered:** {log_entry['error_details']}\n"
        markdown_entry += f"- **Execution Time:** {log_entry['execution_time']}\n"
        markdown_entry += f"- **Outcome:** {log_entry['outcome']}\n"

        # Append to Markdown file
        with open(self.session_log_file, "a") as f:
            f.write(markdown_entry + "\n")

        print(f"✅ Work session logged successfully: {task}")

    def log_ai_execution(self, function, *args, **kwargs):
        """Wraps AI execution to log its behavior."""
        start_time = time.time()
        try:
            result = function(*args, **kwargs)
            execution_time = time.time() - start_time
            self.log_work_session(
                task=f"AI executed {function.__name__}",
                execution_time=execution_time,
                outcome="Success"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            error_trace = traceback.format_exc()
            self.log_work_session(
                task=f"AI executed {function.__name__}",
                execution_time=execution_time,
                error_details=error_trace,
                outcome="Failed"
            )
            return None

    def retrieve_recent_sessions(self, hours=1):
        """Retrieves work session logs from the past `hours`."""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)

        try:
            with open(self.session_log_file, "r") as f:
                logs = f.readlines()
        except FileNotFoundError:
            print("⚠ No previous work sessions found.")
            return []

        recent_logs = []
        for line in logs:
            if line.startswith("## ["):
                timestamp_str = line.split("[")[1].split("]")[0]
                log_time = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                if log_time >= cutoff_time:
                    recent_logs.append(line.strip())

        return recent_logs

# 🚀 Example Usage
if __name__ == "__main__":
    logger = WorkSessionLogger()
    
    # Example AI execution logging
    def sample_ai_task():
        """Mock AI task function."""
        time.sleep(1)
        return "AI completed task successfully."

    logger.log_ai_execution(sample_ai_task)

    # Example manual logging
    logger.log_work_session(
        "Refactored AI work session logging",
        files_changed=["work_session_logger.py", "query_chroma.py"],
        error_details="None",
        execution_time=1.23,
        outcome="Successfully refactored AI logging."
    )

---

# 📂 code_base/agents/architect_agent.py

import os
import requests

class ArchitectAgent:
    """Handles AI architectural planning and system design."""

    KNOWLEDGE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/architect_knowledge"

    def __init__(self):
        self.api_url = "http://localhost:5000/api/task"
        self.load_knowledge()

    def load_knowledge(self):
        """Loads architectural guidelines from the knowledge base."""
        self.knowledge = []
        for file in os.listdir(self.KNOWLEDGE_DIR):
            with open(os.path.join(self.KNOWLEDGE_DIR, file), "r") as f:
                self.knowledge.append(f.read())

    def execute_task(self, task):
        """Processes architectural planning tasks."""
        print(f"🔹 Architect Agent Processing Task: {task}")
        response = requests.post(self.api_url, json={"prompt": task})
        return response.json().get("response", "No response.")

# 🚀 Example Usage
if __name__ == "__main__":
    agent = ArchitectAgent()
    print(agent.execute_task("Define the architecture for an AI-driven self-improving system."))

---

# 📂 code_base/agents/devops_agent.py

import os
import requests

class DevOpsAgent:
    """Handles AI-driven DevOps tasks, such as CI/CD, deployment, and monitoring."""

    KNOWLEDGE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/devops_knowledge"

    def __init__(self):
        self.api_url = "http://localhost:5000/api/task"
        self.load_knowledge()

    def load_knowledge(self):
        """Loads DevOps automation knowledge."""
        self.knowledge = []
        for file in os.listdir(self.KNOWLEDGE_DIR):
            with open(os.path.join(self.KNOWLEDGE_DIR, file), "r") as f:
                self.knowledge.append(f.read())

    def execute_devops_task(self, task):
        """Handles infrastructure, deployment, and monitoring tasks."""
        print(f"🔹 DevOps Agent Processing Task: {task}")
        response = requests.post(self.api_url, json={"prompt": f"Execute this DevOps task:\n\n{task}"})
        return response.json().get("response", "No response.")

# 🚀 Example Usage
if __name__ == "__main__":
    agent = DevOpsAgent()
    print(agent.execute_devops_task("Deploy the latest AI model version."))
---

# 📂 code_base/agents/engineer_agent.py

import os
import requests

class EngineerAgent:
    """Handles AI engineering, feature development, and implementation."""

    KNOWLEDGE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/engineer_knowledge"

    def __init__(self):
        self.api_url = "http://localhost:5000/api/task"
        self.load_knowledge()

    def load_knowledge(self):
        """Loads engineering best practices from the knowledge base."""
        self.knowledge = []
        for file in os.listdir(self.KNOWLEDGE_DIR):
            with open(os.path.join(self.KNOWLEDGE_DIR, file), "r") as f:
                self.knowledge.append(f.read())

    def execute_task(self, task):
        """Processes AI engineering tasks."""
        print(f"🔹 Engineer Agent Processing Task: {task}")
        response = requests.post(self.api_url, json={"prompt": task})
        return response.json().get("response", "No response.")

# 🚀 Example Usage
if __name__ == "__main__":
    agent = EngineerAgent()
    print(agent.execute_task("Develop an API for AI-generated feature requests."))


# --- AI-Generated Code Block ---
from flask import Flask, request, jsonify
import torch
from transformers import pipeline

app = Flask(__name__)
feature_classifier = pipeline("text-classification") # load AI model

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    if 'prompt' not in data:
        return bad_request('must include prompt field')
    
    prompt = data['prompt']
    feature_requests = feature_classifier(prompt) # AI generates the requests
    response = {
        "feature_request": feature_requests[0]["generated_text"]
    } 
        
    return jsonify(response), 201
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request, jsonify
app = Flask(__name__)

feature_requests = []

@app.route('/api/v1/feature_request', methods=['POST'])
def create_feature_request():
    new_request = {
        'id': len(feature_requests) + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
    }
    feature_requests.append(new_request)
    return jsonify({'feature_request': new_request}), 201

if __name__ == '__main__':
    app.run(debug=True)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
import openai # You'll need to install this package via pip (pip install openai)

openai.api_key = "YOUR_OPENAI_API_KEY"

app = Flask(__name__)

@app.route('/generate_feature', methods=['POST'])
def generate_feature():
    data = request.get_json() # Assuming you're passing JSON in the POST body with the feature description

    if 'description' not in data:
        return {"error": "Missing feature description"}, 400

    response = openai.Completion.create(
      model="text-davinci-002", # The model to use for generation
      prompt=f"Generate a new feature request based on this user description: {data['description']}\nNew Feature Request: ",
      temperature=0.7,
      max_tokens=256,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )

    return {"generated_feature": response['choices'][0]['text'].strip()} # Return the generated feature request

if __name__ == '__main__':
   app.run(port = 5000)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
from flask_restful import Resource, Api
import json

app = Flask(__name__)
api = Api(app)

class AIRequestGenerator(Resource):
    def post(self):
        data = request.get_json()  # get data from the post body
        feature_request = generate_feature_request(data['input'])   # assuming you have a function named 'generate_feature_request' that accepts input and returns the AI-generated feature request.
        return {'AI_Feature_Request': feature_request}, 201

api.add_resource(AIRequestGenerator, '/ai/generate')

if __name__ == '__main__':
    app.run(debug=True)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
from transformers import pipeline
import json

app = Flask(__name__)
classifier = pipeline("text-generation")  # initialize the model

@app.route('/generate_feature', methods=['POST'])
def generate_feature():
    data = request.get_json()  # get JSON data from POST request
    text = data['input']  # extract input text from the data
    
    generated_texts = classifier(text)[0]["generated_text"]  # generate feature requests
    
    return json.dumps({"feature": generated_texts}), 200  # return response in JSON format
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
import openai
openai.api_key = "YOUR_OPENAI_API_KEY"

app = Flask(__name__)

@app.route('/generate_feature', methods=['POST'])
def generate_feature():
    data = request.get_json()  # Assuming the client sends JSON
    prompt = "Generate a feature for an AI-powered product" + str(data)
    
    response = openai.Completion.create(
      model="text-davinci-002",
      prompt=prompt,
      temperature=0.7,
      max_tokens=256,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    
    return {"generated_feature": response['choices'][0]['text'].strip()}
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
import openai

app = Flask(__name__)
openai.api_key = "YOUR_OPENAI_API_KEY" # replace with your OpenAI API key

@app.route('/generate-feature', methods=['POST'])
def generate_feature():
    # Parse the request data
    data = request.get_json()

    # Use OpenAI GPT-3 to generate a feature request based on the given prompt
    response = openai.Completion.create(
        engine="davinci",  # or another suitable model
        prompt=f"Create an AI-generated feature request for: {data['prompt']}",
        max_tokens=2048,   # maximum number of tokens to generate in the completion
    )

    return {'feature': response.choices[0].text}

if __name__ == '__main__':
    app.run(debug=True)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/feature_request', methods=['POST'])
def generate_feature():
    data = request.get_json()  # Get the POSTed data
    
    if 'user_input' not in data:
        return jsonify({"message": "No user input provided."}), 400

    user_input = data['user_input']
    feature_request = generate_feature_based_on_ai(user_input)  # Implement this function
    
    return jsonify({'feature': feature_request}), 201

if __name__ == '__main__':
    app.run(debug=True)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
app = Flask(__name__)

# AI model to generate feature requests
ai_model = AI_Model() # Assuming we have an AI Model class that generates feature requests.

@app.route('/feature-request', methods=['POST'])
def generate_feature_request():
    issue = request.json["issue"]  # Assumes the user issues are sent in JSON format
    feature_request = ai_model.generate(issue)
    
    return {"feature_request": feature_request}
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # adjust according to your needs
db = SQLAlchemy(app)

# Define Models
class FeatureRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)

@app.route('/feature-request', methods=['POST'])
def create_feature_request():
    # Generate AI-generated title and description here... 
    ai_title = "AI generated feature request: {}".format(random.randint(1,100))
    ai_description = "This is an auto-generated feature request with id: {}".format(random.randint(1,100))
    
    new_feature_request = FeatureRequest(title=ai_title, description=ai_description)

    db.session.add(new_feature_request)
    db.session.commit()

    return jsonify({'id': new_feature_request.id})

if __name__ == '__main__':
    app.run(debug=True)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# Mock data
feature_requests = [
    {'id': 1, 'title': 'Implement AI-generated feature requests', 'description': 'Create an API endpoint for AI-generated feature requests...'},
]

@app.route('/api/v1/feature_requests', methods=['GET'])
def get_feature_requests():
    return jsonify({'feature_requests': feature_requests})

# This is a placeholder for the AI-generated part
@app.route('/api/v1/generate_feature_request', methods=['POST'])
def generate_feature_request():
    data = request.get_json()
    new_id = random.randint(2, 100)   # Generate a random ID for the feature request
    title = "AI-generated feature request"  # This would normally be generated by AI
    description = "This is an AI-generated feature request..."  # This would also be generated by AI

    new_feature_request = {'id': new_id, 'title': title, 'description': description}
    feature_requests.append(new_feature_request)
    
    return jsonify({'feature_request': new_feature_request}), 201

if __name__ == "__main__":
    app.run(debug=True)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
import openai

# Initialize Flask app
app = Flask(__name__)

openai.api_key = "YOUR_OPENAI_KEY"  # replace with your OpenAI API key

def generate_feature(user_prompt):
    response = openai.Completion.create(
        engine="davinci",
        prompt=f"Generate a software feature based on this description: {user_prompt}\n\nFeature: ",
        temperature=0.7,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"]
    )
    
    return response['choices'][0]['text'].strip()  # return the generated feature text

@app.route('/api/generate-feature', methods=['POST'])
def generate_feature_endpoint():
    user_prompt = request.json['user_request']  # get the prompt from the json body of the post request
    
    try:
        generated_feature = generate_feature(user_prompt)
        
        return {
            "status": "success",
            "generated_feature": generated_feature
        }, 200

    except Exception as e:
        print(e)
        return {"status": "error", "message": str(e)}, 500
    
if __name__ == '__main__':
    app.run(debug=True)
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request
import json

app = Flask(__name__)

# This is a placeholder route for your feature request generation model
@app.route('/generate_feature', methods=['POST'])
def generate_feature():
    data = request.get_json()
    # Here you would implement your AI model to generate a feature request based on the input 'data'
    # For simplicity, let's just return a hardcoded string:
    generated_feature = {'title': 'User Authentication', 'description': 'Implement user authentication'}
    return json.dumps(generated_feature)

if __name__ == "__main__":
    app.run()
# --- End AI-Generated Code Block ---


# --- AI-Generated Code Block ---
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/feature_request', methods=['POST'])
def create_feature():
    # Assuming the request data is JSON and has 'description' field.
    req_data = request.get_json()
    description = req_data.get('description')
    
    # The AI model would be used here to generate a feature request based on the provided description. 
    # But for simplicity, we will just return the same description as feature request.
    # This is where you'd insert your actual AI model code.
    
    generated_feature = description
    return jsonify({'generated_feature': generated_feature}), 201

if __name__ == '__main__':
   app.run(debug=True)
# --- End AI-Generated Code Block ---

---

# 📂 code_base/agents/feedback_agent.py

import os
import requests

class FeedbackAgent:
    """Analyzes AI-generated results & stores performance logs."""

    KNOWLEDGE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/feedback_knowledge"

    def __init__(self):
        self.api_url = "http://localhost:5000/api/task"
        self.load_knowledge()

    def load_knowledge(self):
        """Loads AI evaluation knowledge base."""
        self.knowledge = []
        for file in os.listdir(self.KNOWLEDGE_DIR):
            with open(os.path.join(self.KNOWLEDGE_DIR, file), "r") as f:
                self.knowledge.append(f.read())

    def analyze_result(self, ai_output):
        """Logs AI results and gives feedback."""
        print(f"🔹 Feedback Agent Evaluating AI Output: {ai_output[:100]}...")
        response = requests.post(self.api_url, json={"prompt": f"Provide feedback on this AI-generated output:\n\n{ai_output}"})
        return response.json().get("response", "No response.")

# 🚀 Example Usage
if __name__ == "__main__":
    agent = FeedbackAgent()
    print(agent.analyze_result("AI-generated API documentation"))

---

# 📂 code_base/agents/oversight_agent.py

import os
import requests

class OversightAgent:
    """Ensures AI-generated changes align with system integrity & best practices."""

    KNOWLEDGE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/oversight_knowledge"

    def __init__(self):
        self.api_url = "http://localhost:5000/api/task"
        self.load_knowledge()

    def load_knowledge(self):
        """Loads oversight guidelines from the knowledge base."""
        self.knowledge = []
        for file in os.listdir(self.KNOWLEDGE_DIR):
            with open(os.path.join(self.KNOWLEDGE_DIR, file), "r") as f:
                self.knowledge.append(f.read())

    def validate_code(self, code):
        """Checks if the proposed AI-generated code is valid."""
        print(f"🔹 Oversight Agent Reviewing Code...")
        response = requests.post(self.api_url, json={"prompt": f"Review this code for best practices:\n\n{code}"})
        return response.json().get("response", "No response.")

# 🚀 Example Usage
if __name__ == "__main__":
    agent = OversightAgent()
    print(agent.validate_code("def example():\n    return 'Hello, world'"))

---

# 📂 code_base/agents/qa_agent.py

import os
import requests

class QAAgent:
    """Handles AI-driven software testing, regression, and debugging."""

    KNOWLEDGE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/qa_knowledge"

    def __init__(self):
        self.api_url = "http://localhost:5000/api/task"
        self.load_knowledge()

    def load_knowledge(self):
        """Loads QA guidelines from the knowledge base."""
        self.knowledge = []
        for file in os.listdir(self.KNOWLEDGE_DIR):
            with open(os.path.join(self.KNOWLEDGE_DIR, file), "r") as f:
                self.knowledge.append(f.read())

    def execute_task(self, task):
        """Processes AI QA and debugging tasks."""
        print(f"🔹 QA Agent Processing Task: {task}")
        response = requests.post(self.api_url, json={"prompt": task})
        return response.json().get("response", "No response.")

# 🚀 Example Usage
if __name__ == "__main__":
    agent = QAAgent()
    print(agent.execute_task("Run automated tests on the latest AI-generated API."))

---

# 📂 code_base/agents/reviewer_agent.py

import os
import requests

class ReviewerAgent:
    """Handles AI code reviews, validation, and improvement suggestions."""

    KNOWLEDGE_DIR = "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/reviewer_knowledge"

    def __init__(self):
        self.api_url = "http://localhost:5000/api/task"
        self.load_knowledge()

    def load_knowledge(self):
        """Loads review guidelines from the knowledge base."""
        self.knowledge = []
        for file in os.listdir(self.KNOWLEDGE_DIR):
            with open(os.path.join(self.KNOWLEDGE_DIR, file), "r") as f:
                self.knowledge.append(f.read())

    def execute_task(self, task):
        """Processes AI code review tasks."""
        print(f"🔹 Reviewer Agent Processing Task: {task}")
        response = requests.post(self.api_url, json={"prompt": task})
        return response.json().get("response", "No response.")

# 🚀 Example Usage
if __name__ == "__main__":
    agent = ReviewerAgent()
    print(agent.execute_task("Review the generated API structure for efficiency."))

---

# 📂 code_base/test_scripts/data_processor.py

def process_data(input_data):
    """Processes data but does not handle NoneType values."""
    return input_data["value"] + 10  # ❌ TypeError if 'value' is None

# Simulated test case
data = {"value": None}
process_data(data)  # ❌ Causes TypeError: unsupported operand type(s)

---

# 📂 code_base/test_scripts/math_utilities.py

def calculate_ratio(numerator, denominator):
    """Calculates ratio but does not handle ZeroDivisionError."""
    return numerator / denominator  # ❌ Crashes when denominator = 0

# Simulated test case
result = calculate_ratio(10, 0)  # ❌ Causes ZeroDivisionError

---

# 📂 code_base/test_scripts/test_api_handler.py

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    """Handles a machine learning model prediction request."""
    data = request.get_json()
    result = model.predict(data["input"])  # ❌ model is not defined, causes NameError
    return jsonify({"prediction": result})

if __name__ == "__main__":
    app.run(debug=True)

---

# 📂 code_base/test_scripts/test_db_handler.py

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

def connect_to_database():
    """Attempts to connect to the database but times out."""
    try:
        engine = create_engine('your-db-uri', connect_args={"connect_timeout": 5})  # ❌ Too low timeout
        connection = engine.connect()
        return connection
    except OperationalError as e:
        print(f"Database Connection Failed: {e}")
        return None

---

# 📂 code_base/test_scripts/test_math_operations.py

def divide_numbers(a, b):
    """Performs division but does not handle zero division."""
    return a / b  # ❌ Potential ZeroDivisionError when b = 0

print(divide_numbers(10, 0))  # ❌ This will crash the program

---

# 📂 code_base/test_scripts/user_auth.py

def authenticate_user(user_data):
    """Authenticates a user but throws KeyError if 'username' is missing."""
    return user_data["username"]  # ❌ KeyError if 'username' is missing

# Simulated test case
user_info = {"password": "secure123"}
authenticate_user(user_info)  # ❌ Causes KeyError: 'username'

---

# 📂 scripts/aggregator_search.py

#!/usr/bin/env python3
"""
aggregator_search.py

A "Memory Palace" style aggregator that queries multiple Chroma collections
(knowledge_base, work_sessions, blueprints, blueprint_revisions, execution_logs,
debugging_logs, project_codebase, blueprint_versions) in one shot, using a
384-dim embedding model name so it doesn't mismatch your environment.

Usage:
    python3 aggregator_search.py "division error" [5]
"""

import sys
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

CHROMA_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"

COLLECTIONS_TO_QUERY = [
    "knowledge_base",
    "work_sessions",
    "blueprints",
    "blueprint_revisions",
    "execution_logs",
    "debugging_logs",
    "project_codebase",
    "blueprint_versions",
]

def aggregator_search(query: str, top_n: int = 3):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    q_embed = emb_model.embed_query(query)
    combined_results = []

    for coll_name in COLLECTIONS_TO_QUERY:
        try:
            coll = client.get_or_create_collection(coll_name)
        except Exception as e:
            print(f"⚠ Could not access collection '{coll_name}': {e}")
            continue

        try:
            # get top_n from this domain
            res = coll.query(query_embeddings=[q_embed], n_results=top_n)
        except Exception as e:
            print(f"⚠ Error querying '{coll_name}': {e}")
            continue

        if not res or "documents" not in res or len(res["documents"]) == 0:
            continue

        docs = res["documents"][0]
        metas = res["metadatas"][0] if "metadatas" in res else [{}]*len(docs)
        dists = res.get("distances", [[]])
        if len(dists) > 0 and len(dists[0]) == len(docs):
            dists = dists[0]
        else:
            dists = [9999.0]*len(docs)

        for doc, meta, dist in zip(docs, metas, dists):
            combined_results.append({
                "collection": coll_name,
                "distance": dist,
                "document": doc,
                "metadata": meta
            })

    combined_results.sort(key=lambda x: x["distance"])
    return combined_results[:top_n]

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 aggregator_search.py <query> [n_results]")
        sys.exit(1)

    query_text = sys.argv[1]
    n = 3
    if len(sys.argv) > 2:
        n = int(sys.argv[2])

    results = aggregator_search(query_text, n)

    print(f"\n🔎 Combined aggregator search for: '{query_text}' (top {n} overall)\n")
    for i, r in enumerate(results, start=1):
        c_name = r["collection"]
        dist = r["distance"]
        doc = r["document"]
        meta = r["metadata"] or {}  # safe fallback

        print(f"Result #{i} | Collection: {c_name} | Distance: {dist}")
        print("-------------------------------------------------")
        if not isinstance(meta, dict):
            meta = {}
        for k, v in meta.items():
            print(f"{k}: {v}")

        snippet = doc[:400]
        snippet += "..." if len(doc) > 400 else ""
        print("\nSnippet Preview:")
        print(snippet)
        print("=================================================\n")

if __name__ == "__main__":
    main()

---

# 📂 scripts/blueprint_execution.py

#!/usr/bin/env python3
"""
Blueprint Execution Script with LLM-Generated Improvement Notes

File path:
  /mnt/f/projects/ai-recall-system/scripts/blueprint_execution.py

Imports AgentManager from:
  /mnt/f/projects/ai-recall-system/code_base/agent_manager.py

Integrates:
  - threshold-based logic (catastrophic + ratio approach)
  - LLM-based improvement notes (Deepseek Coder 33B or similar)
"""

import sys
import os

# --- Fix the import path so Python can find 'code_base.agent_manager' ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.append(PARENT_DIR)

# Now we can import from the code_base folder
from code_base.agent_manager import AgentManager

import chromadb
import datetime
import json
import traceback

class BlueprintExecution:
    """
    Manages Blueprint Execution Logs (BELogs), Blueprint Versions, and AI Self-Iteration.
    Includes:
      - log_execution(...) for storing new execution logs
      - generate_blueprint_revision(...) for creating a new BRP when needed
      - get_past_attempts(...) for retrieving older attempts
      - get_latest_blueprint_version(...) for checking the current blueprint version

    Now includes LLM-based improvement notes:
      - We pass an AgentManager to the constructor.
      - If a revision is triggered, we call the LLM to auto-generate notes.
    """

    def __init__(self, agent_manager=None):
        """
        Initialize ChromaDB clients and get or create the relevant collections.
        We'll define logic for thresholds:
          1) Single catastrophic fail threshold
          2) Efficiency threshold
          3) Ratio/average approach
        We'll also store the agent_manager if we want LLM-based improvements.

        Args:
            agent_manager: An instance of AgentManager (or None). If provided,
                           we can call LLM to generate improvement notes.
        """
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        self.execution_logs = self.chroma_client.get_or_create_collection(name="execution_logs")
        self.blueprint_versions = self.chroma_client.get_or_create_collection(name="blueprint_versions")
        self.revision_proposals = self.chroma_client.get_or_create_collection(name="blueprint_revisions")

        # We'll store the agent_manager for LLM calls
        self.agent_manager = agent_manager

        # Dictionary to store specific thresholds for certain tasks or blueprint IDs.
        self.thresholds_map = {}

        # Fallback defaults if the task isn't in self.thresholds_map
        self.DEFAULT_EFFICIENCY_THRESHOLD = 70         # normal sub-threshold
        self.DEFAULT_CATASTROPHIC_THRESHOLD = 30       # single catastrophic fail
        self.DEFAULT_RATIO_WINDOW = 3                  # look at last N runs
        self.DEFAULT_RATIO_FAIL_COUNT = 2              # if 2 out of 3 are "bad," trigger

        print(
            "⚙️ [BlueprintExecution __init__] Default thresholds:\n"
            f"    Efficiency threshold: {self.DEFAULT_EFFICIENCY_THRESHOLD}\n"
            f"    Catastrophic threshold: {self.DEFAULT_CATASTROPHIC_THRESHOLD}\n"
            f"    Ratio window: {self.DEFAULT_RATIO_WINDOW}\n"
            f"    Ratio fail count: {self.DEFAULT_RATIO_FAIL_COUNT}\n"
            "To override these for certain tasks, fill in self.thresholds_map.\n"
            "LLM-based improvement notes are enabled if you pass an agent_manager.\n"
        )

    def log_execution(
            self,
            blueprint_id: str,
            task_name: str,
            execution_context: str,
            expected_outcome: str,
            execution_time: float,
            files_changed: list,
            dependencies: list,
            pipeline_connections: list,
            errors: str,
            success: bool,
            efficiency_score: int,
            improvement_suggestions: str
        ) -> str:
        """
        Logs AI task execution in BELogs with structured metadata (for exact filtering)
        and full JSON text (for semantic search).

        We'll also check for:
        1) Single catastrophic fail (with explicit meltdown phrases)
        2) Ratio/average approach on last N runs
        3) Different thresholds for different tasks or blueprint IDs
        If conditions are met, we automatically propose a blueprint revision.
        We'll call an LLM for improvement notes if self.agent_manager is available.

        Returns:
            str: The unique ID (execution_trace_id) for this new execution log.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        execution_trace_id = f"log_{timestamp.replace(' ', '_')}"

        blueprint_version = self.get_latest_blueprint_version(blueprint_id)
        thresholds = self.get_thresholds_for_task(task_name)
        eff_thresh = thresholds["efficiency_threshold"]
        cat_thresh = thresholds["catastrophic_threshold"]
        ratio_window = thresholds["ratio_window"]
        ratio_fail_count = thresholds["ratio_fail_count"]

        print(
            f"⚙️ [log_execution] For '{task_name}', using these thresholds:\n"
            f"    Efficiency threshold: {eff_thresh}\n"
            f"    Catastrophic threshold: {cat_thresh}\n"
            f"    Ratio window: {ratio_window}\n"
            f"    Ratio fail count: {ratio_fail_count}\n"
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
            "improvement_suggestions": improvement_suggestions or "None"
        }

        # Insert into Chroma: The entire log as "document" plus key metadata
        self.execution_logs.add(
            ids=[execution_trace_id],
            documents=[json.dumps(log_entry)],
            metadatas=[{
                "task_name": task_name,
                "blueprint_id": blueprint_id,
                "timestamp": timestamp,
                "success": success,
                "errors_encountered": errors or "None",
                "efficiency_score": int(efficiency_score)
            }]
        )

        print(f"✅ Execution log stored: {execution_trace_id}")

        # ---------------------------------------------------
        # AUTOMATED BLUEPRINT REVISION PROPOSAL LOGIC
        # ---------------------------------------------------

        meltdown_phrases = ["catastrophic meltdown", "catastrophic error", "catastrophic failure"]
        is_catastrophic = False
        if efficiency_score < cat_thresh:
            is_catastrophic = True
        else:
            if errors:
                check_lower = errors.lower()
                for phrase in meltdown_phrases:
                    if phrase in check_lower:
                        is_catastrophic = True
                        break

        # Ratio-based approach
        recent_runs = past_attempts[-(ratio_window - 1):] if ratio_window > 1 else []
        run_data = []
        for attempt in recent_runs:
            run_data.append({
                "success": attempt["success"],
                "efficiency_score": attempt["efficiency_score"]
            })
        run_data.append({
            "success": success,
            "efficiency_score": efficiency_score
        })

        bad_count = 0
        sum_eff = 0
        for rd in run_data:
            sum_eff += rd["efficiency_score"]
            if (not rd["success"]) or (rd["efficiency_score"] < eff_thresh):
                bad_count += 1

        avg_efficiency = sum_eff / len(run_data) if run_data else 100
        repeated_failures = (bad_count >= ratio_fail_count) or (avg_efficiency < eff_thresh)

        reason_string = ""
        revision_triggered = False

        if is_catastrophic:
            revision_triggered = True
            reason_string += (f"[Catastrophic fail] efficiency={efficiency_score} < {cat_thresh} "
                            f"or meltdown phrase in errors={errors}. ")
        elif repeated_failures:
            revision_triggered = True
            reason_string += (f"[Ratio check] Among last {len(run_data)} runs, {bad_count} were bad "
                            f"(eff < {eff_thresh} or success=False). avg_eff={avg_efficiency:.1f}.")

        if revision_triggered:
            # We'll incorporate an LLM prompt if self.agent_manager is available
            if self.agent_manager:
                print("⚙️ [LLM] Generating improvement notes via LLM... please wait.")
                llm_notes = self.build_llm_improvement_notes(
                    blueprint_id=blueprint_id,
                    logs=run_data,
                    reason=reason_string
                )
                # ******** KEY CHANGE ********
                # Prepend the ratio/catastrophic string to the LLM bullet points
                improvement_notes = f"{reason_string}\n\n(LLM-based) {llm_notes}"
            else:
                improvement_notes = f"(Auto) {reason_string}"

            print(f"⚠️  [Revision Trigger] {reason_string}")
            self.generate_blueprint_revision(blueprint_id, improvement_notes)

        return execution_trace_id


    def build_llm_improvement_notes(self, blueprint_id, logs, reason) -> str:
        """
        Calls the LLM (via self.agent_manager) to produce improvement notes
        for the revision proposal. We'll feed it a short prompt describing the 'reason'
        plus some info about the logs.

        We refine the prompt to be concise yet robust, focusing on solutions,
        avoiding disclaimers or filler text.
        """
        # Summarize logs in brief
        logs_summary = ""
        for idx, run in enumerate(logs):
            logs_summary += (f"\n• Run #{idx+1}: success={run['success']}, "
                             f"eff={run['efficiency_score']}")

        # A refined prompt for your advanced debugging approach
        # We keep it concise but thorough
        prompt_text = (
            "You are an AI blueprint improver. You review AI system logs and propose short, direct improvements.\n"
            "Your suggestions should be bullet points with no extraneous disclaimers.\n\n"
            "Project context:\n"
            "We have an advanced AI recall system used for code debugging and workflow optimization.\n"
            "We want to remain scalable, handle repeated or catastrophic fails, and keep logic maintainable.\n\n"
            f"Blueprint ID: {blueprint_id}\n"
            f"Reason for Proposed Revision:\n{reason}\n"
            f"Relevant Recent Logs:\n{logs_summary}\n\n"
            "Please list precise improvements or next steps the AI system can take to address these issues. "
            "Keep it bullet-pointed and pragmatic. No disclaimers, no apologies, no repeated statements."
        )

        if not self.agent_manager:
            return f"(LLM not available) {reason}"

        try:
            llm_response = self.agent_manager.send_task("architect", prompt_text, timeout=60)
            if not llm_response or not llm_response.strip():
                return f"(LLM returned nothing) {reason}"
            return llm_response.strip()
        except Exception as e:
            return f"(LLM error: {e}) {reason}"

    def get_thresholds_for_task(self, task_name: str) -> dict:
        """
        Pulls out the thresholds for a given task from self.thresholds_map.
        If none found, fallback to default.
        """
        if task_name in self.thresholds_map:
            custom = self.thresholds_map[task_name]
            return {
                "efficiency_threshold": custom.get("efficiency_threshold", self.DEFAULT_EFFICIENCY_THRESHOLD),
                "catastrophic_threshold": custom.get("catastrophic_threshold", self.DEFAULT_CATASTROPHIC_THRESHOLD),
                "ratio_window": custom.get("ratio_window", self.DEFAULT_RATIO_WINDOW),
                "ratio_fail_count": custom.get("ratio_fail_count", self.DEFAULT_RATIO_FAIL_COUNT)
            }
        else:
            return {
                "efficiency_threshold": self.DEFAULT_EFFICIENCY_THRESHOLD,
                "catastrophic_threshold": self.DEFAULT_CATASTROPHIC_THRESHOLD,
                "ratio_window": self.DEFAULT_RATIO_WINDOW,
                "ratio_fail_count": self.DEFAULT_RATIO_FAIL_COUNT
            }

    def get_latest_blueprint_version(self, blueprint_id: str) -> str:
        """
        Retrieves the latest version of a given blueprint using metadata filtering.
        If none found, defaults to "v1.0".
        """
        results = self.blueprint_versions.get(
            where={"blueprint_id": blueprint_id},
            limit=1
        )
        if results and "documents" in results and results["documents"]:
            latest_version_doc = json.loads(results["documents"][0])
            return latest_version_doc.get("blueprint_version", "v1.0")
        return "v1.0"

    def get_past_attempts(self, task_name: str, limit=10) -> list:
        """
        Retrieves past execution logs for a given task by filtering on metadata.
        We'll just show summary lines for debugging. We won't do the full JSON dump.
        """
        print(f"\n🔍 Debugging `get_past_attempts()` for task: {task_name}")

        results = self.execution_logs.get(
            where={"task_name": task_name},
            limit=limit
        )

        if not results or "documents" not in results or not results["documents"]:
            print("⚠ No execution logs retrieved by metadata filter.")
            return []

        past_attempts = []
        for doc in results["documents"]:
            log_data = json.loads(doc)
            stored_task_name = log_data.get("task_name", "UNKNOWN")
            short_str = (
                f"  → Found attempt '{log_data.get('execution_trace_id','NOID')}' "
                f"success={log_data.get('success')} eff={log_data.get('efficiency_score')}"
            )
            print(short_str)
            if stored_task_name.strip().lower() == task_name.strip().lower():
                past_attempts.append(log_data)

        print(f"✅ Found {len(past_attempts)} matching past execution attempts.")
        return past_attempts

    def generate_blueprint_revision(self, blueprint_id: str, improvement_notes: str) -> str:
        """
        Creates a Blueprint Revision Proposal (BRP) when AI detects repeated failures
        or sub-threshold performance or catastrophic fail.

        The revision_id is "brp_{blueprint_id}" for simplicity, but you could
        incorporate a version # or timestamp if you like.
        """
        revision_id = f"brp_{blueprint_id}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        revision_entry = {
            "revision_id": revision_id,
            "timestamp": timestamp,
            "blueprint_id": blueprint_id,
            "improvement_notes": improvement_notes,
            "status": "Pending Review"
        }

        self.revision_proposals.add(
            ids=[revision_id],
            documents=[json.dumps(revision_entry)],
            metadatas=[{"blueprint_id": blueprint_id}]
        )
        print(f"🔹 Blueprint Revision Proposal Generated: {revision_id}")
        return revision_id

# -----------------------------------------------------------
# Example usage to test this script
# -----------------------------------------------------------
if __name__ == "__main__":
    # We'll create an AgentManager for LLM usage
    agent_mgr = AgentManager()

    # Pass it to our BlueprintExecution
    blueprint_exec = BlueprintExecution(agent_manager=agent_mgr)

    # We'll define specialized thresholds for "Refactor query logic in query_chroma.py"
    blueprint_exec.thresholds_map["Refactor query logic in query_chroma.py"] = {
        "efficiency_threshold": 75,
        "catastrophic_threshold": 25,
        "ratio_window": 3,
        "ratio_fail_count": 2
    }

    print("=== Example 1: A normal run above threshold ===")
    exec_id_1 = blueprint_exec.log_execution(
        blueprint_id="bp_003",
        task_name="Refactor query logic in query_chroma.py",
        execution_context="Normal test scenario",
        expected_outcome="Ensure we pass the threshold",
        execution_time=1.5,
        files_changed=["query_chroma.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="None",
        success=True,
        efficiency_score=80,
        improvement_suggestions="Just verifying normal pass."
    )

    print("=== Example 2: A catastrophic fail scenario ===")
    exec_id_2 = blueprint_exec.log_execution(
        blueprint_id="bp_003",
        task_name="Refactor query logic in query_chroma.py",
        execution_context="Testing catastrophic scenario",
        expected_outcome="Should fail drastically",
        execution_time=2.0,
        files_changed=["query_chroma.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="Catastrophic meltdown: index out of range",
        success=False,
        efficiency_score=20,
        improvement_suggestions="Needs immediate fix."
    )

    print("=== Example 3: Repeated sub-threshold test ===")
    exec_id_3 = blueprint_exec.log_execution(
        blueprint_id="bp_003",
        task_name="Refactor query logic in query_chroma.py",
        execution_context="2 out of last 3 sub-threshold",
        expected_outcome="We want to see ratio approach trigger a revision",
        execution_time=2.1,
        files_changed=["query_chroma.py"],
        dependencies=[],
        pipeline_connections=[],
        errors="Some minor error, not meltdown",
        success=False,
        efficiency_score=60,
        improvement_suggestions="Possible concurrency fix needed."
    )

    print("\n=== Checking final logs for 'Refactor query logic in query_chroma.py' ===")
    final_logs = blueprint_exec.get_past_attempts("Refactor query logic in query_chroma.py")
    print(f"Retrieved {len(final_logs)} attempts in total.")

---

# 📂 scripts/capture_git_changes.py

import subprocess
import datetime

def get_git_changes():
    """Retrieves all unstaged & staged changes from Git."""
    try:
        diff_output = subprocess.run(["git", "diff"], capture_output=True, text=True).stdout
        staged_output = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True).stdout
        return diff_output, staged_output
    except Exception as e:
        return f"Error retrieving Git changes: {e}", ""

def log_git_changes():
    """Logs git changes into work session log."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diff, staged = get_git_changes()

    log_entry = f"## [{timestamp}] Code Changes\n"
    if diff.strip():
        log_entry += f"🔹 **Unstaged Changes:**\n```\n{diff}\n```\n"
    if staged.strip():
        log_entry += f"🔹 **Staged Changes:**\n```\n{staged}\n```\n"

    with open("../logs/work_session.md", "a") as f:
        f.write(log_entry + "\n")

    print("✅ Git changes logged successfully.")

if __name__ == "__main__":
    log_git_changes()

---

# 📂 scripts/check_doc_count.py

import chromadb

def check_doc_count(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db", collection_name="project_codebase"):
    client = chromadb.PersistentClient(path=chroma_path)
    coll = client.get_collection(collection_name)
    data = coll.get()
    print(f"Found {len(data['documents'])} docs in '{collection_name}'")

if __name__ == "__main__":
    check_doc_count()

---

# 📂 scripts/cleanup_collections.py

import chromadb

# def delete_code_collections(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db"):
#     client = chromadb.PersistentClient(path=chroma_path)
    
#     # Print existing collections for reference
#     collections = client.list_collections()
#     print("🔎 Current collections in Chroma:")
#     for c in collections:
#         print(f" - {c}")

#     # The ones you want to remove
#     to_remove = {"project_codebase"}

#     # Try to delete them if they exist
#     for c in collections:
#         if c in to_remove:
#             try:
#                 client.delete_collection(c)
#                 print(f"✅ Deleted collection '{c}'")
#             except Exception as e:
#                 print(f"❌ Could not delete '{c}': {e}")

#     # Re-list collections after deletion
#     print("\n🔎 Collections after attempted deletion:")
#     collections_after = client.list_collections()
#     for c in collections_after:
#         print(f" - {c}")

# if __name__ == "__main__":
#     delete_code_collections()


def inspect_collections(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db"):
    client = chromadb.PersistentClient(path=chroma_path)
    
    all_coll = client.list_collections()
    for coll_name in all_coll:
        coll = client.get_collection(coll_name)
        # Query some stats. If you just call coll.get() with no filter, you can see how many docs we have.
        data = coll.get()
        doc_count = len(data["documents"])
        print(f"Collection: {coll_name} => {doc_count} documents")

if __name__ == "__main__":
    inspect_collections()


---

# 📂 scripts/compiled_knowledge.py

import os
import datetime
import re

# Dynamically resolve the absolute path to ai-recall-system
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base")
OUTPUT_FILE = os.path.join(BASE_DIR, "compiled_knowledge.md")

def slugify(text):
    """
    Converts a string to a slug suitable for markdown anchor links.
    """
    text = text.lower()
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    return text

def generate_table_of_contents(markdown_files):
    """
    Creates a markdown formatted table of contents with links to each file's section.
    """
    toc_lines = ["# Table of Contents", ""]
    for filename in markdown_files:
        title = os.path.splitext(filename)[0]
        anchor = slugify(title)
        toc_lines.append(f"- [{title}](#{anchor})")
    toc_lines.append("")  # add a blank line at the end
    return "\n".join(toc_lines)

def merge_markdown_files(source_folder, output_file):
    """Merges all markdown files in a folder into a single, well-formatted document."""
    if not os.path.exists(source_folder):
        print(f"❌ ERROR: Source folder '{source_folder}' does not exist.")
        return

    # Get a sorted list of markdown files
    md_files = sorted([f for f in os.listdir(source_folder) if f.endswith(".md") and os.path.isfile(os.path.join(source_folder, f))])
    
    # Prepare a timestamp for the document header
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"# Compiled Knowledge Base\n\n_Last updated: {timestamp}_\n\n"
    
    # Generate a table of contents
    toc = generate_table_of_contents(md_files)
    
    # Open the output file for writing (this will overwrite previous contents)
    with open(output_file, "w", encoding="utf-8") as outfile:
        # Write the header and TOC
        outfile.write(header)
        outfile.write(toc)
        outfile.write("\n\n---\n\n")
        
        # Process each markdown file
        for filename in md_files:
            file_path = os.path.join(source_folder, filename)
            with open(file_path, "r", encoding="utf-8") as infile:
                title = os.path.splitext(filename)[0]
                anchor = slugify(title)
                # Write a section header with an anchor
                outfile.write(f"\n\n# {title}\n")
                outfile.write(f"<a name=\"{anchor}\"></a>\n\n")
                outfile.write(infile.read())
                outfile.write("\n\n---\n")
    
    print(f"✅ All markdown files merged into: {output_file}")

# Execute with resolved paths
merge_markdown_files(KNOWLEDGE_BASE_DIR, OUTPUT_FILE)

---

# 📂 scripts/debug_chroma.py

import chromadb

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

def dump_raw_data(collection_name):
    """Dump raw stored documents in a collection."""
    collection = chroma_client.get_or_create_collection(name=collection_name)
    results = collection.get()

    print(f"\n📌 RAW DATA IN '{collection_name}':")
    for doc in results["documents"]:
        print(f"🔹 Stored Entry: {repr(doc)}")  # Show EXACT format

if __name__ == "__main__":
    for collection in ["blueprints", "debugging_logs", "execution_logs", "work_sessions", "knowledge_base"]:
        dump_raw_data(collection)

---

# 📂 scripts/dependencies_compiler.py

import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
CODEBASE_DIRS = [os.path.join(BASE_DIR, "code_base"), os.path.join(BASE_DIR, "scripts")]
OUTPUT_FILE = os.path.join(BASE_DIR, "dependencies_report.md")

def extract_imports_from_file(file_path):
    """Extracts import statements from a Python file."""
    imports = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)", line)
            if match:
                imports.add(match.group(1))
    return imports

def generate_dependency_report(output_file):
    """Scans the codebase for dependencies and writes them to a report."""
    dependencies = set()
    for directory in CODEBASE_DIRS:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    dependencies.update(extract_imports_from_file(file_path))

    # Write results to a markdown file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 📦 AI Recall System - Dependencies Report\n\n")
        f.write("## 🔹 Identified Python Dependencies\n")
        for dep in sorted(dependencies):
            f.write(f"- `{dep}`\n")

    print(f"✅ Dependencies report saved to {output_file}")

if __name__ == "__main__":
    generate_dependency_report(OUTPUT_FILE)

---

# 📂 scripts/generate_codebase_inventory.py

import os

# Define paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODEBASE_DIRS = [os.path.join(BASE_DIR, "code_base"), os.path.join(BASE_DIR, "scripts")]
OUTPUT_FILE = os.path.join(BASE_DIR, "codebase_inventory.md")
TREE_OUTPUT = os.path.join(BASE_DIR, "codebase_structure.txt")

def generate_directory_tree(output_file, depth=3):
    """Generate a tree structure of the codebase."""
    os.system(f"tree -L {depth} --dirsfirst --filelimit 50 {BASE_DIR} > {output_file}")

def merge_python_files(output_file):
    """Merge all Python scripts from `code_base/` and `scripts/` into a single markdown file."""
    with open(output_file, "w", encoding="utf-8") as outfile:
        for directory in CODEBASE_DIRS:
            for root, _, files in os.walk(directory):
                for file in sorted(files):
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        outfile.write(f"\n# 📂 {file_path.replace(BASE_DIR + '/', '')}\n\n")
                        with open(file_path, "r", encoding="utf-8") as infile:
                            outfile.write(infile.read())
                        outfile.write("\n---\n")  # Separator between files
    print(f"✅ Codebase inventory saved to {output_file}")

if __name__ == "__main__":
    print("🔄 Generating directory tree...")
    generate_directory_tree(TREE_OUTPUT)
    
    print("🔄 Merging Python scripts into a single file...")
    merge_python_files(OUTPUT_FILE)

    print(f"✅ Directory tree saved to {TREE_OUTPUT}")
    print(f"✅ Codebase inventory saved to {OUTPUT_FILE}")

---

# 📂 scripts/index_codebase.py

#!/usr/bin/env python3
"""
index_codebase.py

Indexes your entire project (or selected subdirs) into ChromaDB, chunking files
and storing them with stable doc_ids that incorporate a hash of the chunk.
- If a chunk is unchanged, it won't be duplicated.
- If a chunk changes, a new doc_id is created, preserving the old version.

This script can be safely run multiple times; only changed/new chunks get added.

NOTE: We explicitly set model_name="sentence-transformers/all-MiniLM-L6-v2"
(384-dimensional) so it matches your older logs/blueprints. That prevents
dimension mismatch in aggregator_search.
"""

import os
import sys
import hashlib
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
# If you get an import error, do: pip install -U langchain-community

###############################################################################
# 1) CONFIGURABLE CONSTANTS
###############################################################################

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"

CHUNK_SIZE = 300  # lines or words
CHUNK_OVERLAP = 50  # only used if line-based is False
ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".txt", ".yml", ".toml"}
SKIP_DIRS = {"chroma_db", ".git", "__pycache__", ".idea", "venv"}
SKIP_FILES = {"codebase_inventory.md", "compiled_knowledge.md"}

ROOT_DIRS = [
    "/mnt/f/projects/ai-recall-system/code_base",
    "/mnt/f/projects/ai-recall-system/knowledge_base",
    "/mnt/f/projects/ai-recall-system/scripts",
]

# If True, chunk by lines. If False, chunk by words (with overlap).
LINE_BASED_CHUNKING = False

###############################################################################
# 2) HELPER FUNCTIONS
###############################################################################

def compute_md5_hash(text: str) -> str:
    normalized = text.strip().replace("\r\n", "\n")
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

def chunk_by_lines(full_text: str, chunk_size: int = 300):
    lines = full_text.splitlines()
    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk_slice = lines[i : i + chunk_size]
        chunk_str = "\n".join(chunk_slice)
        chunks.append(chunk_str)
    return chunks

def chunk_by_words(full_text: str, chunk_size=300, overlap=50):
    words = full_text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = words[start:end]
        chunk_str = " ".join(chunk)
        if chunk_str.strip():
            chunks.append(chunk_str)
        start += (chunk_size - overlap)
    return chunks

###############################################################################
# 3) MAIN INDEX FUNCTION
###############################################################################

def index_codebase():
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' ...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # Use 384-dim model so aggregator_search is consistent across logs + code
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total_new_chunks = 0
    total_files = 0

    for root_dir in ROOT_DIRS:
        if not os.path.exists(root_dir):
            print(f"⚠ Root dir not found: {root_dir}. Skipping.")
            continue

        for current_root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    continue
                if filename in SKIP_FILES:
                    continue

                filepath = os.path.join(current_root, filename)
                rel_path = os.path.relpath(filepath, start=root_dir)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception as e:
                    print(f"⚠ Error reading {filepath}: {e}")
                    continue

                if not text.strip():
                    continue
                total_files += 1

                # chunk
                if LINE_BASED_CHUNKING:
                    chunks = chunk_by_lines(text, CHUNK_SIZE)
                else:
                    chunks = chunk_by_words(text, CHUNK_SIZE, CHUNK_OVERLAP)

                new_chunks_for_file = 0
                for idx, chunk_str in enumerate(chunks):
                    if not chunk_str.strip():
                        continue
                    chunk_hash = compute_md5_hash(chunk_str)
                    doc_id = f"{filepath}::chunk_{idx}::hash_{chunk_hash}"

                    existing = collection.get(ids=[doc_id])
                    if existing and existing["ids"]:
                        continue

                    embedding = embed_model.embed_documents([chunk_str])[0]
                    meta = {
                        "filepath": filepath,
                        "rel_path": rel_path,
                        "chunk_index": idx,
                        "hash": chunk_hash,
                        "mod_time": os.path.getmtime(filepath),
                    }
                    collection.add(
                        documents=[chunk_str],
                        embeddings=[embedding],
                        metadatas=[meta],
                        ids=[doc_id]
                    )
                    new_chunks_for_file += 1

                if new_chunks_for_file > 0:
                    print(f"   ⮑ Indexed {new_chunks_for_file} new chunk(s) from {filepath}")
                    total_new_chunks += new_chunks_for_file

    print(f"\n✅ Done indexing. Processed {total_files} files total. Added {total_new_chunks} new chunks.")

###############################################################################
# 4) ENTRY POINT
###############################################################################

if __name__ == "__main__":
    index_codebase()

---

# 📂 scripts/initialize_chroma.py

import chromadb

# Initialize ChromaDB in WSL-compatible path
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

# Define collections
collections = {
    "blueprints": "Stores AI project blueprints and recursive blueprint revisions.",
    "debugging_logs": "Logs AI debugging sessions, fixes, and error resolutions.",
    "execution_logs": "Tracks AI task execution history and outcomes.",
    "work_sessions": "Stores AI work sessions, timestamps, and activity logs.",
    "knowledge_base": "General AI memory storage (guidelines, best practices, key learnings)."
}

# Create collections if they don’t exist
for name, description in collections.items():
    collection = chroma_client.get_or_create_collection(name=name)
    print(f"✅ Collection '{name}' initialized: {description}")

---

# 📂 scripts/log_work_session.py

import chromadb
import datetime
import json

chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
collection = chroma_client.get_or_create_collection(name="work_sessions")

def log_work_session(description, files_changed=None, error_fixed=None, result=None):
    """Logs work session in ChromaDB and work_session.md."""
    log_data = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "description": description,
        "files_changed": files_changed or [],
        "error_fixed": error_fixed,
        "result": result
    }

    # Store log in ChromaDB
    collection.add(ids=[log_data["timestamp"]], documents=[json.dumps(log_data)])

    # Also store in markdown file
    log_entry = f"## [{log_data['timestamp']}] {description}\n"
    if files_changed:
        log_entry += f"- **Files Changed:** {', '.join(files_changed)}\n"
    if error_fixed:
        log_entry += f"- **Error Fixed:** {error_fixed}\n"
    if result:
        log_entry += f"- **Result:** {result}\n"

    with open("../logs/work_session.md", "a") as f:
        f.write(log_entry + "\n")

    print("✅ Work session logged successfully.")

if __name__ == "__main__":
    log_work_session(
        "Refactored AI recall system",
        files_changed=["query_chroma.py", "work_session_logger.py"],
        error_fixed="Optimized retrieval filtering",
        result="Blueprint recall now works correctly."
    )

---

# 📂 scripts/query_chroma.py

import chromadb
import json

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
execution_logs = chroma_client.get_or_create_collection(name="execution_logs")
blueprint_versions = chroma_client.get_or_create_collection(name="blueprint_versions")
revision_proposals = chroma_client.get_or_create_collection(name="blueprint_revisions")
work_sessions = chroma_client.get_or_create_collection(name="work_sessions")
debugging_logs = chroma_client.get_or_create_collection(name="debugging_logs")

def list_execution_logs(limit=100):
    """Retrieve and print a summary of stored execution logs."""
    results = execution_logs.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No execution logs found in ChromaDB.")
        return

    print("\n📌 Stored Execution Logs in ChromaDB (summary):")
    for doc in results["documents"]:
        log_data = json.loads(doc)
        task_name = log_data.get("task_name", "UNKNOWN")
        exc_id = log_data.get("execution_trace_id", "NO_ID")
        success = log_data.get("success")
        efficiency = log_data.get("efficiency_score")
        short_str = (f" - [ExecID: {exc_id}] Task={task_name}, success={success}, "
                     f"eff={efficiency}")
        print(short_str)

def list_revision_proposals(limit=50):
    """Retrieve and print a summary of stored Blueprint Revision Proposals."""
    results = revision_proposals.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No blueprint revision proposals found in ChromaDB.")
        return

    print("\n📌 Stored Blueprint Revision Proposals (summary):")
    for doc in results["documents"]:
        rev_data = json.loads(doc)
        rev_id = rev_data.get("revision_id")
        bpid = rev_data.get("blueprint_id")
        status = rev_data.get("status")
        short_str = (f" - [RevID: {rev_id}] For blueprint={bpid}, status={status}")
        print(short_str)

def list_work_sessions(limit=50):
    """Retrieve and print a summary of stored work session logs."""
    results = work_sessions.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No work sessions found in ChromaDB.")
        return

    print("\n📌 Stored Work Session Logs (summary):")
    for doc in results["documents"]:
        sess_data = json.loads(doc)
        sid = sess_data.get("id") or sess_data.get("timestamp")
        outcome = sess_data.get("outcome", "N/A")
        short_str = f" - [SessionID: {sid}] outcome={outcome}"
        print(short_str)

def list_debugging_logs(limit=50):
    """Retrieve and print a summary of stored debugging logs."""
    results = debugging_logs.get(limit=limit)

    if not results or "documents" not in results or not results["documents"]:
        print("⚠ No debugging logs found in ChromaDB.")
        return

    print("\n📌 Stored Debugging Logs (summary):")
    for doc in results["documents"]:
        dbg_data = json.loads(doc)
        dbgid = dbg_data.get("id") or dbg_data.get("timestamp")
        error_msg = dbg_data.get("error_message", "N/A")
        short_str = f" - [DebugID: {dbgid}] error={error_msg}"
        print(short_str)

def get_work_sessions(limit=5):
    """Retrieve the last N AI work sessions from ChromaDB (raw)."""
    results = work_sessions.get(limit=limit)
    return [json.loads(doc) for doc in results["documents"]] if results and "documents" in results else []

def get_past_execution_attempts(task_name, limit=10):
    """
    Retrieve past execution logs for a given task (metadata filter).
    We'll return them as raw dicts for possible further usage,
    but we won't print them fully here.
    """
    results = execution_logs.get(where={"task_name": task_name}, limit=limit)

    if not results or "documents" not in results:
        return []

    return [json.loads(doc) for doc in results["documents"]]

if __name__ == "__main__":
    print("\n🔹 Blueprints:")

    # Execution logs
    list_execution_logs()

    # Revision proposals
    list_revision_proposals()

    # Work sessions
    list_work_sessions()

    # Debug logs
    list_debugging_logs()

    # Example: retrieve raw logs for a certain task
    print("\n🔹 Work Session Logs from ChromaDB:", get_work_sessions())
    print(f"\n🔍 Past Execution Attempts for 'Refactor query logic in query_chroma.py':")
    matching_runs = get_past_execution_attempts(task_name="Refactor query logic in query_chroma.py")
    print(matching_runs)  # if you want a raw print

---

# 📂 scripts/query_codebase_chunks.py

#!/usr/bin/env python3
"""
query_codebase_chunks.py

Simple retrieval from the "project_codebase" ChromaDB collection
based on naive substring matching or metadata filtering.

If you want semantic search, you can replace with an embedding-based approach
using e.g. langchain or chroma client embedding queries.
"""

import sys
import os
import json
import chromadb

# Where is the project root
PROJECT_ROOT = "/mnt/f/projects/ai-recall-system"
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "project_codebase"

def naive_substring_search(docs, query):
    """
    Basic substring search over chunk text.
    If you want vector similarity, switch to an embedding query.
    """
    results = []
    for i, doc_text in enumerate(docs["documents"]):
        if query.lower() in doc_text.lower():
            meta = docs["metadatas"][i]
            doc_id = docs["ids"][i]
            results.append({
                "doc_id": doc_id,
                "relative_path": meta["relative_path"],
                "chunk_index": meta["chunk_index"],
                "file_type": meta["file_type"],
                "snippet": doc_text[:300] + ("..." if len(doc_text) > 300 else "")
            })
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python query_codebase_chunks.py \"search term\"")
        sys.exit(1)

    query = sys.argv[1]
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    # For demo, we just fetch all docs (limit=9999) and do naive substring search
    # In a big codebase, this is NOT efficient. We can do real embeddings or chunk filtering.
    results = collection.get(limit=9999)

    if not results or "documents" not in results or not results["documents"]:
        print(f"No codebase chunks found in collection '{COLLECTION_NAME}'.")
        return

    # naive substring search
    matched = naive_substring_search(results, query)
    if not matched:
        print(f"No matches for query: '{query}'")
        return

    print(f"\n🔹 Found {len(matched)} matches for '{query}':\n")
    for m in matched[:10]:  # show first 10
        print(f"Doc ID: {m['doc_id']}")
        print(f"Path: {m['relative_path']}")
        print(f"Type: {m['file_type']}")
        print(f"Snippet: {m['snippet']}\n{'-'*60}")

if __name__ == "__main__":
    main()

---

# 📂 scripts/retrieve_codebase.py

#!/usr/bin/env python3
"""
retrieve_codebase.py

Queries your 'project_codebase' collection in ChromaDB to find relevant code/doc
chunks using embeddings. This aligns with the new index_codebase.py approach
(word-based or line-based chunking, stable doc_ids, hashed chunks, etc.).

Usage:
   python3 retrieve_codebase.py "division error" 5

Which will retrieve the top 5 matching chunks for "division error".
"""

import sys
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"

def retrieve_code_snippets(query: str, n_results: int = 3):
    """
    Performs an embedding-based semantic search over 'project_codebase' in Chroma.
    Returns a list of (doc_content, metadata) tuples.
    """
    # 1) Connect to Chroma
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # 2) Load embeddings model (same as used when indexing)
    emb = HuggingFaceEmbeddings()
    query_embedding = emb.embed_query(query)

    # 3) Query the collection by embedding
    #    This uses semantic similarity to find relevant chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    matched_chunks = []
    if results and "documents" in results:
        # Typically results["documents"] is a list of lists
        # We'll iterate the top-level list => results["documents"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        for doc, meta in zip(docs, metas):
            matched_chunks.append((doc, meta))

    return matched_chunks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 retrieve_codebase.py <query> [n_results]")
        sys.exit(1)

    query_text = sys.argv[1]
    n = 3
    if len(sys.argv) > 2:
        n = int(sys.argv[2])

    snippets = retrieve_code_snippets(query_text, n_results=n)

    print(f"\n🔍 Found {len(snippets)} relevant chunks for: '{query_text}'\n")
    for i, (doc, meta) in enumerate(snippets, start=1):
        filepath = meta.get("filepath", "??")
        rel_path = meta.get("rel_path", "??")
        chunk_idx = meta.get("chunk_index", "??")
        mod_time = meta.get("mod_time", "??")
        print(f"Result #{i}")
        print("-------------------------------------------------")
        print(f"Filepath: {filepath}")
        print(f"Rel path: {rel_path}")
        print(f"Chunk #:  {chunk_idx}")
        print(f"Last mod: {mod_time}")
        print()
        print("Snippet Content (first 400 chars):")
        print(doc[:400] + ("..." if len(doc) > 400 else ""))
        print("=================================================\n")

---

# 📂 scripts/store_test_data.py

import chromadb
import json

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

# Define test data
test_data = {
    "blueprints": {
        "id": "blueprint_001",
        "name": "AI Debugging Strategy v1",
        "version": "1.0",
        "description": "Defines AI debugging recall process."
    },
    "debugging_logs": {
        "id": "debug_001",
        "timestamp": "2025-02-14T12:30:00",
        "error_message": "SQL Integrity Constraint Violation",
        "fix_attempted": "Added unique constraint to schema."
    },
    "execution_logs": {
        "id": "execution_001",
        "task": "Retrieve debugging logs",
        "timestamp": "2025-02-14T13:00:00",
        "execution_success": True,
        "duration": 1.2
    },
    "work_sessions": {
        "id": "session_001",
        "session_name": "AI Work Session 1",
        "start_time": "2025-02-14T10:00:00",
        "end_time": "2025-02-14T12:00:00",
        "tasks_completed": ["Blueprint Retrieval", "ChromaDB Initialization"]
    },
    "knowledge_base": {
        "id": "kb_001",
        "category": "Coding Best Practices",
        "content": "Always use snake_case for function names in Python.",
        "last_updated": "2025-02-14T11:45:00"
    }
}

# Overwrite old collections to prevent duplicates
for collection_name in test_data.keys():
    chroma_client.delete_collection(name=collection_name)  # Force delete bad data
    collection = chroma_client.get_or_create_collection(name=collection_name)

    # Convert dictionary to proper JSON before storing
    json_document = json.dumps(test_data[collection_name], ensure_ascii=False)
    
    print(f"📌 Storing in {collection_name}: {json_document}")  # Verify correct format
    collection.add(ids=[test_data[collection_name]["id"]], documents=[json_document])

print("✅ Test data stored successfully in ChromaDB with proper JSON formatting!")

---
