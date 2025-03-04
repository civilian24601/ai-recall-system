
# 📂 code_base/__init__.py


---

# 📂 code_base/agent.py


---

# 📂 code_base/agent_manager.py

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

---

# 📂 code_base/api_structure.py

# /mnt/f/projects/ai-recall-system/code_base/api_structure.py

import requests
from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS
from network_utils import detect_api_url  # <-- Now we can import the same logic if we want

app = Flask(__name__)
CORS(app)
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
import hashlib
import os
import logging

import chromadb  # For storing snippet strategies in Chroma

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DebuggingStrategy:
    """Manages AI debugging strategies and tracks effectiveness."""

    def __init__(self, test_mode=False):
        # [UPDATED] Switch file paths if test_mode
        if test_mode:
            self.debug_logs_file = "tests/test_logs/debug_logs_test.json"
            self.strategy_log_file = "tests/test_logs/debugging_strategy_log_test.json"
        else:
            self.debug_logs_file = "../logs/debug_logs.json"
            self.strategy_log_file = "../logs/debugging_strategy_log.json"

        # Connect to Chroma for snippet success rates
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        
        # [SAME AS BEFORE] 
        self.strategies_collection_name = (
            "debugging_strategies_test" if test_mode else "debugging_strategies"
        )
        self.strategies_collection = self.chroma_client.get_or_create_collection(
            name=self.strategies_collection_name
        )

    def load_strategy_logs(self):
        """Loads past debugging strategies from local JSON."""
        try:
            with open(self.strategy_log_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load strategy logs: {e}")
            return []  # Return empty if file missing or corrupted

    def save_strategy_logs(self, strategies):
        """Saves updated debugging strategies to local JSON."""
        try:
            with open(self.strategy_log_file, "w") as f:
                json.dump(strategies, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save strategy logs: {e}")

    def normalize_snippet(self, snippet):
        """
        Removes triple backticks, 'python', extra blank lines, and trailing whitespace
        to deduplicate near-identical fix attempts.
        """
        if not snippet:
            return ""
        snippet = snippet.replace("```", "")
        snippet = snippet.replace("python", "")
        lines = [line.strip() for line in snippet.split("\n") if line.strip()]
        return "\n".join(lines)

    def build_strategy_doc_id(self, error_type, snippet):
        """
        Creates a unique ID for each error_type + snippet combo,
        e.g. via hashing to keep it short.
        """
        unique_str = f"{error_type}::{snippet}"
        doc_id = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()[:16]
        return doc_id

    def sync_strategy_with_chroma(self, error_type, snippet, strategy_record):
        """
        Upserts the snippet strategy record into the 'debugging_strategies' or
        'debugging_strategies_test' collection.
        """
        try:
            doc_id = self.build_strategy_doc_id(error_type, snippet)
            doc_json = json.dumps(strategy_record)

            # Minimal metadata for searching
            metadata = {
                "error_type": error_type,
                "snippet_hash": doc_id,
                "attempts": strategy_record.get("attempts", 0),
                "success_rate": strategy_record.get("success_rate", 0.0),
            }

            existing_docs = self.strategies_collection.get(ids=[doc_id])
            if existing_docs and "documents" in existing_docs and existing_docs["documents"]:
                logging.info(f"Strategy doc ID '{doc_id}' already exists. Updating existing entry.")
                self.strategies_collection.update(
                    ids=[doc_id],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
            else:
                self.strategies_collection.add(
                    ids=[doc_id],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
            logging.info(f"Synced strategy doc ID '{doc_id}' to Chroma collection '{self.strategies_collection_name}'.")
        except Exception as e:
            logging.error(f"Failed to sync strategy with Chroma: {e}")

    def get_debugging_strategy(self, error_type):
        """
        Returns the snippet with highest success_rate for error_type,
        or a default fallback if none found in local JSON. 
        (No direct Chroma query for single best snippet yet.)
        """
        try:
            strategies = self.load_strategy_logs()
            matching_strategies = [s for s in strategies if s["error_type"] == error_type]

            if matching_strategies:
                best_strategy = sorted(
                    matching_strategies,
                    key=lambda x: x["success_rate"],
                    reverse=True
                )[0]
                return best_strategy["strategy"]

            # Default fallback
            return "Standard debugging: AI will analyze logs, suggest fixes, and request verification."
        except Exception as e:
            logging.error(f"Failed to get debugging strategy: {e}")
            return "Standard debugging: AI will analyze logs, suggest fixes, and request verification."

    def update_strategy(self, error_type, snippet, success):
        """
        Updates or creates a debugging strategy record based on
        the new fix attempt's success. Also upserts into Chroma.
        """
        try:
            strategies = self.load_strategy_logs()

            # Normalize snippet to reduce duplicates
            norm_snippet = self.normalize_snippet(snippet)

            for entry in strategies:
                # Match both error_type and the EXACT snippet
                if entry["error_type"] == error_type and entry["strategy"] == norm_snippet:
                    entry["attempts"] += 1
                    if success:
                        entry["successful_fixes"] += 1
                    entry["success_rate"] = entry["successful_fixes"] / entry["attempts"]

                    self.save_strategy_logs(strategies)
                    self.sync_strategy_with_chroma(error_type, norm_snippet, entry)
                    return

            # If no matching entry, create a new one
            new_record = {
                "error_type": error_type,
                "strategy": norm_snippet,
                "attempts": 1,
                "successful_fixes": 1 if success else 0,
                "success_rate": 1.0 if success else 0.0
            }
            strategies.append(new_record)
            self.save_strategy_logs(strategies)

            # Upsert to Chroma
            self.sync_strategy_with_chroma(error_type, norm_snippet, new_record)
        except Exception as e:
            logging.error(f"Failed to update strategy: {e}")

    def analyze_previous_fixes(self):
        """
        Reads debug_logs.json, updates snippet success records for each fix attempt.
        Normalizes the snippet to reduce duplicates, then upserts to local + Chroma.
        """
        try:
            with open(self.debug_logs_file, "r") as f:
                debug_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Failed to load debug logs: {e}")
            return

        for entry in debug_logs:
            if "error" in entry and "fix_attempted" in entry:
                logging.info(f"Processing error log: {entry['error']}")
                success_flag = (entry.get("fix_successful") is True)
                norm_snippet = self.normalize_snippet(entry["fix_attempted"])
                self.update_strategy(entry["error"], norm_snippet, success=success_flag)

# 🚀 Example Usage
if __name__ == "__main__":
    debugger = DebuggingStrategy(test_mode=False)
    debugger.analyze_previous_fixes()
    # Optionally retrieve best known snippet for some error
    best_snippet = debugger.get_debugging_strategy("ZeroDivisionError: division by zero")
    print(f"Best known snippet for ZeroDivisionError: {best_snippet}")

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
import logging
import chromadb

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the parent directory of code_base to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .agent_manager import AgentManager
from .debugging_strategy import DebuggingStrategy  # [NEW] We import it here so we can link them

class SingleAgentWorkflow:
    """Executes AI recall, debugging, and code retrieval workflows in single-agent mode."""

    def __init__(self, test_mode=False):
        """
        If test_mode=True, we switch to test logs and 'debugging_logs_test' for Chroma.
        Otherwise, we use 'debug_logs.json' & 'debugging_logs' for production.
        """
        self.agent_manager = AgentManager()
        
        # [NEW] Switch local JSON path based on test_mode
        if test_mode:
            self.debug_log_file = "tests/test_logs/debug_logs_test.json"
        else:
            self.debug_log_file = "../logs/debug_logs.json"

        self.test_scripts_dir = "./test_scripts/"
        self.ai_timeout = 300

        # Initialize Chroma client for debug logs
        self.chroma_client = chromadb.PersistentClient(
            path="/mnt/f/projects/ai-recall-system/chroma_db/"
        )
        
        # [NEW] Pick test vs. production collection name
        self.debug_collection_name = "debugging_logs_test" if test_mode else "debugging_logs"
        self.debugging_logs_collection = self.chroma_client.get_or_create_collection(
            name=self.debug_collection_name
        )

        # [NEW] Also create a DebuggingStrategy instance, using the same test_mode
        self.debugging_strategy = DebuggingStrategy(test_mode=test_mode)

    def generate_log_id(self, prefix="log"):
        """Generates a unique ID for debugging log entries."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{timestamp}"

    def retrieve_past_debug_logs(self):
        """Retrieve past debugging logs from local storage."""
        logging.info("Retrieving past debugging logs...")
        try:
            with open(self.debug_log_file, "r") as f:
                logs = json.load(f)
                valid_logs = []
                for log in logs:
                    if "id" in log and "error" in log and "stack_trace" in log:
                        valid_logs.append(log)
                    else:
                        logging.warning(f"Skipping invalid log entry: {log}")
                if not valid_logs:
                    logging.warning("No valid debugging logs found.")
                    return []
                logging.info(f"Retrieved {len(valid_logs)} valid logs.")
                return valid_logs
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Debugging log file missing or corrupted. Error: {e}")
            return []

    def sync_debug_log_with_chroma(self, entry):
        """
        Upserts the updated debug log entry into the 'debugging_logs' (or 'debugging_logs_test') collection.
        Each entry is stored as a separate document with ID = entry["id"].
        """
        try:
            doc_json = json.dumps(entry)
            metadata = {
                "error": entry.get("error", ""),
                "timestamp": entry.get("timestamp", ""),
                "resolved": entry.get("resolved", False),
                "fix_successful": entry.get("fix_successful", False),
            }
            existing_docs = self.debugging_logs_collection.get(ids=[entry["id"]])
            if (existing_docs 
                and "documents" in existing_docs 
                and existing_docs["documents"]):
                self.debugging_logs_collection.update(
                    ids=[entry["id"]],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
                logging.info(f"Updated log entry '{entry['id']}' in Chroma collection '{self.debug_collection_name}'.")
            else:
                self.debugging_logs_collection.add(
                    ids=[entry["id"]],
                    documents=[doc_json],
                    metadatas=[metadata]
                )
                logging.info(f"Added new log entry '{entry['id']}' to Chroma collection '{self.debug_collection_name}'.")
        except Exception as e:
            logging.error(f"Failed to sync debug log with Chroma: {e}")

    def run_workflow(self):
        """Executes a structured AI debugging & recall workflow for ALL pending issues."""
        logging.info("Starting Single-Agent AI Workflow...")

        past_debug_logs = self.retrieve_past_debug_logs()
        if not past_debug_logs:
            logging.error("No past debugging logs available.")
            return

        logging.info("Checking for unresolved debugging issues...")
        unresolved_logs = [
            log for log in past_debug_logs
            if log.get("resolved") is False and "stack_trace" in log
        ]

        if not unresolved_logs:
            logging.info("No unresolved debugging issues found.")
            return

        logging.info(f"Found {len(unresolved_logs)} unresolved logs to process.")

        for error_entry in unresolved_logs:
            script_name = None
            stack_trace = error_entry.get("stack_trace", "")
            # e.g. "File 'test_db_handler.py', line 9, in connect_to_database"
            # We'll parse out the script name by splitting on quotes
            parts = stack_trace.split("'")
            if len(parts) >= 2:
                script_name = parts[1]

            if not script_name:
                logging.warning(f"Skipping log entry with missing `stack_trace`: {error_entry}")
                continue

            logging.info(f"AI will attempt to fix `{script_name}` based on debugging logs.")

            script_path = os.path.join(self.test_scripts_dir, script_name)
            script_content = ""
            if os.path.exists(script_path):
                with open(script_path, "r") as f:
                    script_content = f.read()

            if not script_content.strip():
                logging.warning(f"`{script_name}` is empty or unavailable. Skipping AI fix.")
                continue

            logging.info("AI Analyzing Debugging Logs...")
            ai_fix_suggestion = self.agent_manager.delegate_task(
                "debug",
                (
                    f"Analyze `{script_name}` and find the source of the following error: {error_entry['error']}. "
                    "Your response MUST ONLY contain the corrected function inside triple backticks (```python ...```), NO explanations.\n"
                    f"Here is the current content of `{script_name}`:\n"
                    "```python\n"
                    f"{script_content}\n"
                    "```"
                ),
                timeout=self.ai_timeout
            )

            extracted_fix = self.agent_manager.preprocess_ai_response(ai_fix_suggestion)

            logging.info(f"AI Suggested Fix:\n{extracted_fix}\n")
            confirmation = input("Did the fix work? (y/n): ").strip().lower()
            fix_verified = (confirmation == "y")

            # Update the local JSON record
            error_entry["fix_attempted"] = extracted_fix
            error_entry["resolved"] = fix_verified
            error_entry["fix_successful"] = fix_verified

            # For logging, optionally set a timestamp if missing
            if "timestamp" not in error_entry:
                error_entry["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            try:
                # Update local JSON
                with open(self.debug_log_file, "r") as f:
                    logs = json.load(f)

                for i, entry in enumerate(logs):
                    if entry["id"] == error_entry["id"]:
                        logs[i] = error_entry  # Update existing log entry

                with open(self.debug_log_file, "w") as f:
                    json.dump(logs, f, indent=4)

                logging.info("Debugging log successfully updated in `debug_logs.json`.")

                # **UPSET to Chroma** (real-time sync)
                self.sync_debug_log_with_chroma(error_entry)

            except Exception as e:
                logging.error(f"Failed to update debugging log: {e}")

            # [NEW] Also update the DebuggingStrategy with success/fail 
            # if we have a recognized 'error' and an AI snippet
            if "error" in error_entry and extracted_fix:
                logging.info("Updating the debugging strategy with fix success/failure...")
                self.debugging_strategy.update_strategy(
                    error_type=error_entry["error"],
                    snippet=extracted_fix,
                    success=fix_verified
                )

        logging.info("Single-Agent AI Workflow Completed!")

# 🚀 Example Usage
if __name__ == "__main__":
    # For production: test_mode=False
    workflow = SingleAgentWorkflow(test_mode=False)
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
import time
import traceback

import chromadb

from .network_utils import detect_api_url

class WorkSessionLogger:
    """Handles AI work session logging, retrieval, and structured summaries."""

    def __init__(self, test_mode=False):  # [CHANGED] add test_mode param
        """
        If test_mode=True, we write to 'tests/test_logs/work_session_test.md'
        and use 'work_sessions_test' collection. Otherwise we do the production path.
        """
        if test_mode:
            self.session_log_file = "tests/test_logs/work_session_test.md"  # [NEW]
            collection_name = "work_sessions_test"                           # [NEW]
        else:
            self.session_log_file = "../logs/work_session.md"
            collection_name = "work_sessions"

        self.chroma_client = chromadb.PersistentClient(
            path="/mnt/f/projects/ai-recall-system/chroma_db/"
        )
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)

        self.api_url = detect_api_url()
        print(f"🔹 Using API URL: {self.api_url}, test_mode={test_mode}")

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
        self.collection.add(
            ids=[timestamp],
            documents=[json.dumps(log_entry)]
        )

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
        """
        Wraps an AI function execution to automatically log timing,
        success/failure, and any errors encountered.
        """
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
        """Retrieves work session logs from the past `hours` by parsing the Markdown file."""
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

# Example usage
if __name__ == "__main__":
    logger = WorkSessionLogger(test_mode=False)

    def sample_ai_task():
        time.sleep(1)
        return "AI completed task successfully."

    logger.log_ai_execution(sample_ai_task)
    logger.log_work_session(
        task="Refactored AI work session logging",
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
aggregator_search.py (Advanced with dedup)

We unify embedding + naive results in "both" mode, but we deduplicate if the
same doc_id / same collection is found from both approaches, picking the one
with the lower distance so the doc appears only once in final output.

Usage:
   python aggregator_search.py "division error" [top_n] [--mode naive|both]
"""

import sys
import chromadb
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
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

def naive_substring_search(docs_dict, query, coll_name):
    """
    Return list of:
       {"collection": coll_name, "distance": 9.0 + rank, "document": doc_text, "metadata": meta, "doc_id": <the doc id>}
    """
    results = []
    all_docs = docs_dict["documents"]
    all_metas = docs_dict["metadatas"]
    all_ids = docs_dict["ids"]
    query_lower = query.lower()

    rank = 0
    for doc_text, meta, doc_id in zip(all_docs, all_metas, all_ids):
        if query_lower in doc_text.lower():
            # We'll do pseudo-dist = 9 + rank
            distance = 9.0 + rank
            if not isinstance(meta, dict):
                meta = {}
            results.append({
                "collection": coll_name,
                "doc_id": doc_id,
                "distance": distance,
                "document": doc_text,
                "metadata": meta
            })
            rank += 1
    return results

def aggregator_search(query, top_n=3, mode="embedding"):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # We'll store final results in "combined_results" but also deduplicate by (collection, doc_id).
    combined_map = {}  # key=(collection, doc_id), value= best record

    # We fetch top_n * 3 from each collection if embedding is used:
    fetch_count = top_n * 3 if mode in ("embedding", "both") else 0

    if mode in ("embedding", "both"):
        # We'll embed once:
        query_embed = emb_model.embed_query(query)

    for coll_name in COLLECTIONS_TO_QUERY:
        try:
            coll = client.get_or_create_collection(coll_name)
        except Exception as e:
            print(f"⚠ Could not access collection '{coll_name}': {e}")
            continue

        # A) Embedding approach
        if mode in ("embedding", "both"):
            try:
                res = coll.query(query_embeddings=[query_embed], n_results=fetch_count)
            except Exception as e:
                print(f"⚠ Error (embedding) in '{coll_name}': {e}")
                res = None

            if res and "documents" in res and res["documents"]:
                docs = res["documents"][0]
                metas = res["metadatas"][0] if "metadatas" in res else [{}]*len(docs)
                dists = res.get("distances", [[]])
                if dists and len(dists) > 0 and len(dists[0]) == len(docs):
                    dists = dists[0]
                else:
                    dists = [9999.0]*len(docs)

                ids = res["ids"][0] if "ids" in res else []
                for doc_text, meta, dist, doc_id in zip(docs, metas, dists, ids):
                    if not isinstance(meta, dict):
                        meta = {}
                    # Boost guideline chunks slightly in embedding results
                    if meta.get("guideline", False):
                        dist = max(0, dist - 0.1)  # Small boost, cap at 0 to avoid negative distances
                    # Force naive-only docs to stay out of embedding rankings
                    if meta.get("naive_only", False) and dist < 9.0:
                        dist = 9.0  # Ensures naive docs rank via substring only
                    key = (coll_name, doc_id)
                    # If we have a record for this key, keep the best (lowest dist)
                    if key not in combined_map or dist < combined_map[key]["distance"]:
                        combined_map[key] = {
                            "collection": coll_name,
                            "doc_id": doc_id,
                            "distance": dist,
                            "document": doc_text,
                            "metadata": meta
                        }

        # B) Naive substring approach
        if mode in ("naive", "both"):
            try:
                naive_docs = coll.get(limit=9999)
            except Exception as e:
                print(f"⚠ Error (naive get) in '{coll_name}': {e}")
                naive_docs = None

            if naive_docs and "documents" in naive_docs and naive_docs["documents"]:
                naive_results = naive_substring_search(naive_docs, query, coll_name)
                for r in naive_results:
                    key = (r["collection"], r["doc_id"])
                    # If no record or distance is bigger in combined_map, update
                    if key not in combined_map or r["distance"] < combined_map[key]["distance"]:
                        combined_map[key] = r

    # Now unify them, sort by ascending distance
    combined_list = list(combined_map.values())
    combined_list.sort(key=lambda x: x["distance"])

    # final top_n overall
    return combined_list[:top_n]

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python aggregator_search.py <query> [top_n] [--mode naive|both]")
        sys.exit(1)

    query_text = args[0]
    top_n = 3
    mode = "embedding"  # default

    # parse second arg
    if len(args) > 1:
        if args[1].isdigit():
            top_n = int(args[1])
        elif args[1].startswith("--mode"):
            pass
        else:
            if args[1] in ("naive","both"):
                mode = args[1]

    # parse optional --mode
    if "--mode" in args:
        idx = args.index("--mode")
        if idx+1 < len(args):
            possible_mode = args[idx+1]
            if possible_mode in ("naive","both"):
                mode = possible_mode

    results = aggregator_search(query_text, top_n, mode)

    print(f"\n🔎 aggregator_search for: '{query_text}' (mode={mode}, top {top_n} overall)\n")
    for i, r in enumerate(results, start=1):
        c_name = r["collection"]
        dist = r["distance"]
        doc = r["document"]
        meta = r["metadata"] or {}
        doc_id = r["doc_id"]

        # if dist>=9 => substring
        dist_str = f"{dist:.4f}"
        if dist >= 9.0:
            # e.g. substring => dist=9 + rank
            # we can do a custom marker
            dist_str = f"(subRank~{int(dist-9)})"

        print(f"Result #{i} | Collection: {c_name} | doc_id: {doc_id} | distance: {dist_str}")
        print("-------------------------------------------------")
        for k,v in meta.items():
            print(f"{k}: {v}")
        snippet = doc[:300]
        if len(doc)>300:
            snippet += "..."
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
    """

    def __init__(self, agent_manager=None, test_mode=False):  # [CHANGED] add test_mode=False
        """
        If test_mode=True, we write to test collections:
          execution_logs_test, blueprint_versions_test, blueprint_revisions_test
        Otherwise, we use production ones: execution_logs, blueprint_versions, blueprint_revisions
        """
        self.chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
        
        # [NEW] choose test vs production collections
        if test_mode:
            self.execution_logs = self.chroma_client.get_or_create_collection(name="execution_logs_test")
            self.blueprint_versions = self.chroma_client.get_or_create_collection(name="blueprint_versions_test")
            self.revision_proposals = self.chroma_client.get_or_create_collection(name="blueprint_revisions_test")
        else:
            self.execution_logs = self.chroma_client.get_or_create_collection(name="execution_logs")
            self.blueprint_versions = self.chroma_client.get_or_create_collection(name="blueprint_versions")
            self.revision_proposals = self.chroma_client.get_or_create_collection(name="blueprint_revisions")

        # We'll store the agent_manager for LLM calls
        self.agent_manager = agent_manager
        self.test_mode = test_mode  # [NEW] keep track if we need it later

        # Dictionary to store specific thresholds for certain tasks or blueprint IDs
        self.thresholds_map = {}

        # Fallback defaults
        self.DEFAULT_EFFICIENCY_THRESHOLD = 70
        self.DEFAULT_CATASTROPHIC_THRESHOLD = 30
        self.DEFAULT_RATIO_WINDOW = 3
        self.DEFAULT_RATIO_FAIL_COUNT = 2

        print(
            "⚙️ [BlueprintExecution __init__] Default thresholds:\n"
            f"    Efficiency threshold: {self.DEFAULT_EFFICIENCY_THRESHOLD}\n"
            f"    Catastrophic threshold: {self.DEFAULT_CATASTROPHIC_THRESHOLD}\n"
            f"    Ratio window: {self.DEFAULT_RATIO_WINDOW}\n"
            f"    Ratio fail count: {self.DEFAULT_RATIO_FAIL_COUNT}\n"
            f"test_mode={test_mode}, so using "
            f"{'execution_logs_test, blueprint_versions_test, blueprint_revisions_test' if test_mode else 'execution_logs, blueprint_versions, blueprint_revisions'}\n"
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
        Logs AI task execution in BELogs with structured metadata (for exact filtering).
        Then checks thresholds and possibly triggers a blueprint revision.
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
            f"⚙️ [log_execution] For '{task_name}', using thresholds:\n"
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

        # ------------- AUTOMATED BLUEPRINT REVISION PROPOSAL LOGIC -------------
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
            reason_string += (f"[Catastrophic fail] eff={efficiency_score} < {cat_thresh} "
                              f"or meltdown phrase in errors={errors}. ")
        elif repeated_failures:
            revision_triggered = True
            reason_string += (f"[Ratio check] Among last {len(run_data)} runs, {bad_count} were bad "
                              f"(eff < {eff_thresh} or success=False). avg_eff={avg_efficiency:.1f}.")

        if revision_triggered:
            if self.agent_manager:
                print("⚙️ [LLM] Generating improvement notes via LLM... please wait.")
                llm_notes = self.build_llm_improvement_notes(
                    blueprint_id=blueprint_id,
                    logs=run_data,
                    reason=reason_string
                )
                improvement_notes = f"{reason_string}\n\n(LLM-based) {llm_notes}"
            else:
                improvement_notes = f"(Auto) {reason_string}"

            print(f"⚠️  [Revision Trigger] {reason_string}")
            self.generate_blueprint_revision(blueprint_id, improvement_notes)

        return execution_trace_id

    def build_llm_improvement_notes(self, blueprint_id, logs, reason) -> str:
        """Calls the LLM (via self.agent_manager) to produce improvement notes."""
        logs_summary = ""
        for idx, run in enumerate(logs):
            logs_summary += (f"\n• Run #{idx+1}: success={run['success']}, eff={run['efficiency_score']}")

        prompt_text = (
            "You are an AI blueprint improver. You review AI system logs and propose short, direct improvements.\n"
            "No disclaimers, no repeated statements.\n\n"
            f"Blueprint ID: {blueprint_id}\n"
            f"Reason for Proposed Revision:\n{reason}\n"
            f"Relevant Recent Logs:\n{logs_summary}\n\n"
            "Please list bullet-pointed improvements or next steps."
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
        """Pull out thresholds for this task from self.thresholds_map, or use defaults."""
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
        """Retrieves the latest version of a given blueprint or 'v1.0' if none found."""
        results = self.blueprint_versions.get(where={"blueprint_id": blueprint_id}, limit=1)
        if results and "documents" in results and results["documents"]:
            latest_version_doc = json.loads(results["documents"][0])
            return latest_version_doc.get("blueprint_version", "v1.0")
        return "v1.0"

    def get_past_attempts(self, task_name: str, limit=10) -> list:
        """Retrieves past logs for a given task from the execution_logs collection."""
        print(f"\n🔍 Debugging get_past_attempts() for task: {task_name}")

        results = self.execution_logs.get(where={"task_name": task_name}, limit=limit)
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
        """Creates a Blueprint Revision Proposal (BRP) in the revision_proposals collection."""
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
# Example usage to test this script manually (not required)
# -----------------------------------------------------------
if __name__ == "__main__":
    agent_mgr = AgentManager()
    blueprint_exec = BlueprintExecution(agent_manager=agent_mgr, test_mode=False)
    ...

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

# 📂 scripts/clear_chroma_duplicates.py

import chromadb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Chroma client
chroma_client = chromadb.PersistentClient(
    path="/mnt/f/projects/ai-recall-system/chroma_db/"
)
debugging_logs_collection = chroma_client.get_or_create_collection(name="debugging_logs")

def clear_duplicates():
    """Clear duplicate entries from the ChromaDB collection."""
    logging.info("Retrieving all entries from ChromaDB collection...")
    all_entries = debugging_logs_collection.get()

    if not all_entries or "documents" not in all_entries:
        logging.info("No entries found in ChromaDB collection.")
        return

    documents = all_entries["documents"]
    ids = all_entries["ids"]
    unique_ids = set()
    duplicates = []

    for doc_id, doc in zip(ids, documents):
        if doc_id in unique_ids:
            duplicates.append(doc_id)
        else:
            unique_ids.add(doc_id)

    if not duplicates:
        logging.info("No duplicate entries found.")
        return

    logging.info(f"Found {len(duplicates)} duplicate entries. Removing duplicates...")
    debugging_logs_collection.delete(ids=duplicates)
    logging.info("Duplicates removed successfully.")

if __name__ == "__main__":
    clear_duplicates()
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

def generate_directory_tree(output_file, depth=5):
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

 - Uses line-based chunking for all files, including .py (no AST for simplicity).
 - For large chunks, we split line-based with overlap.
 - For non-Python files (JS, TS, MD, JSON, etc.), we do line-based chunking with line-range metadata.
   - Special handling for .md: smaller chunk size (100 lines) + 20-line overlap.
   - Markdowns in 'knowledge_base' folder get a 'guideline': True metadata flag.
 - We store 'start_line','end_line','function_name','class_name','node_type' in metadata, ensuring no None values.
 - Watchers with debouncing for partial saves, rename & delete handling.
 - Root directory covers the entire project ("/mnt/f/projects/ai-recall-system").
 
Usage:
    python index_codebase.py
        (one-shot indexing)
    python index_codebase.py --watch
        (start watchers in real-time)
"""

import os
import sys
import time
import hashlib
import threading
import ast

import chromadb
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

import watchdog.events
import watchdog.observers
from watchdog.events import FileSystemEventHandler

##############################################################################
# CONFIG
##############################################################################

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"

CHUNK_SIZE_DEFAULT = 300    # lines, for most files
CHUNK_SIZE_MD = 100         # smaller chunk size for markdown files
CHUNK_OVERLAP_PY = 50       # only used when chunking large Python files
CHUNK_OVERLAP_MD = 20       # overlap for markdown files
ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".txt", ".yml", ".toml", ".js", ".ts"}
SKIP_DIRS = {
    "chroma_db", ".git", "__pycache__", ".idea", "venv", ".pytest_cache", 
    "node_modules", ".next", "dist"
}
SKIP_FILES = {"codebase_inventory.md", "compiled_knowledge.md"}

ROOT_DIRS = ["/mnt/f/projects/ai-recall-system"]  # Index entire project
DEBOUNCE_SECONDS = 2.0

# If AST parse fails, do we fallback to line-based chunking for .py? We'll say yes:
LINE_BASED_CHUNKING_PY_FALLBACK = True

##############################################################################
# UTILS
##############################################################################

def compute_md5_hash(text: str) -> str:
    normalized = text.strip().replace("\r\n", "\n")
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

def chunk_lines_with_range(lines, start_idx, chunk_size=300, overlap=0):
    """
    Takes a list of lines (strings) and returns a list of
    (chunk_text, start_line, end_line).
    If overlap > 0, we do partial overlap.
    """
    i = 0
    results = []
    n = len(lines)
    while i < n:
        end = min(i + chunk_size, n)
        chunk_slice = lines[i:end]
        chunk_text = "\n".join(chunk_slice)
        real_start = start_idx + i
        real_end = start_idx + end - 1

        results.append((chunk_text, real_start, real_end))
        if overlap == 0:
            i = end
        else:
            i += (chunk_size - overlap)
    return results

##############################################################################
# PYTHON AST CHUNKING (Kept for reference, unused now)
##############################################################################

class PyFunctionChunk:
    def __init__(self, name, start_line, end_line, node_type="function", parent_class=None):
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.node_type = node_type
        self.parent_class = parent_class

def parse_python_ast(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    try:
        tree = ast.parse(code)
    except Exception as e:
        print(f"⚠ AST parse error in {filepath}: {e}")
        return []

    results = []
    class ASTVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            parent_cls = getattr(node, "_parent_class", None)
            name = node.name
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            node_type = "function" if not parent_cls else "method"
            results.append(PyFunctionChunk(name, start_line, end_line, node_type, parent_cls))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            parent_cls = getattr(node, "_parent_class", None)
            name = node.name
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            node_type = "async_function" if not parent_cls else "async_method"
            results.append(PyFunctionChunk(name, start_line, end_line, node_type, parent_cls))
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            class_name = node.name
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            results.append(PyFunctionChunk(class_name, start_line, end_line, "class"))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    child._parent_class = class_name
            self.generic_visit(node)

    ASTVisitor().visit(tree)
    return results

def build_python_chunks(lines, func_chunk):
    start_idx = func_chunk.start_line - 1
    end_idx = func_chunk.end_line
    snippet_lines = lines[start_idx:end_idx]

    big_chunks = chunk_lines_with_range(snippet_lines, start_idx, CHUNK_SIZE_DEFAULT, overlap=CHUNK_OVERLAP_PY)
    output = []
    for (chunk_text, real_start, real_end) in big_chunks:
        output.append({
            "text": chunk_text,
            "start_line": real_start + 1,
            "end_line": real_end + 1,
            "function_name": func_chunk.name if func_chunk.node_type in ("function","method","async_function","async_method") else "",
            "class_name": func_chunk.parent_class if func_chunk.parent_class else (func_chunk.name if func_chunk.node_type=="class" else ""),
            "node_type": func_chunk.node_type
        })
    return output

##############################################################################
# reindex_single_file
##############################################################################

def reindex_single_file(filepath, collection, embed_model):
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return 0
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return 0
    if os.path.basename(filepath) in SKIP_FILES:
        return 0

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        print(f"⚠ Error reading {filepath}: {e}")
        return 0

    if not text.strip():
        return 0

    # Remove old doc_ids for this file
    existing_results = collection.get(limit=9999)
    if existing_results and "ids" in existing_results and existing_results["ids"]:
        matched_ids = []
        for doc_id in existing_results["ids"]:
            if doc_id.startswith(f"{filepath}::chunk_"):
                matched_ids.append(doc_id)
        if matched_ids:
            collection.delete(ids=matched_ids)
            print(f"   🔸 Removed {len(matched_ids)} old chunk(s) for updated file: {filepath}")

    lines = text.splitlines()
    new_chunks_for_file = 0

    # Use line-based chunking for all files, including .py
    chunk_size = CHUNK_SIZE_MD if ext == ".md" else CHUNK_SIZE_DEFAULT
    overlap = CHUNK_OVERLAP_MD if ext == ".md" else CHUNK_OVERLAP_PY
    line_blocks = chunk_lines_with_range(lines, 0, chunk_size=chunk_size, overlap=overlap)
    for idx, (chunk_text, st_line, end_line) in enumerate(line_blocks):
        if not chunk_text.strip():
            continue
        chunk_hash = compute_md5_hash(chunk_text)
        doc_id = f"{filepath}::chunk_{idx}::hash_{chunk_hash}"

        embedding = embed_model.embed_documents([chunk_text])[0]

        meta = {
            "filepath": filepath,
            "rel_path": filepath,
            "chunk_index": idx,
            "hash": chunk_hash,
            "mod_time": os.path.getmtime(filepath),
            "start_line": int(st_line),
            "end_line": int(end_line),
            "function_name": "",
            "class_name": "",
            "node_type": "lines",
            "guideline": True if (ext == ".md" and "knowledge_base" in filepath) else False,
            "naive_only": True if ext != ".md" else False  # Naive-only for non-markdown non-Python
        }

        collection.add(
            documents=[chunk_text],
            embeddings=[embedding],
            metadatas=[meta],
            ids=[doc_id]
        )
        new_chunks_for_file += 1

    if new_chunks_for_file > 0:
        print(f"   ⮑ Re-indexed {new_chunks_for_file} chunk(s) from {filepath}")

    return new_chunks_for_file

##############################################################################
# One-shot indexing
##############################################################################

def index_codebase():
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' ...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total_files = 0
    total_new_chunks = 0

    for root_dir in ROOT_DIRS:
        if not os.path.exists(root_dir):
            print(f"⚠ Root dir not found: {root_dir}. Skipping.")
            continue

        for current_root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                filepath = os.path.join(current_root, filename)
                added = reindex_single_file(filepath, collection, embed_model)
                if added > 0:
                    total_files += 1
                    total_new_chunks += added

    print(f"\n✅ Done indexing. Processed {total_files} files total. Added {total_new_chunks} new chunks.")

##############################################################################
# Watchers
##############################################################################

class CodebaseEventHandler(FileSystemEventHandler):
    def __init__(self, collection, embed_model):
        super().__init__()
        self.collection = collection
        self.embed_model = embed_model
        self._pending_changes = {}
        self._lock = threading.Lock()

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            print(f"\n🔄 File renamed from {event.src_path} -> {event.dest_path}")
            self.remove_file_chunks(event.src_path)
            ext = os.path.splitext(event.dest_path)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                self._handle_change(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"\n❌ File deleted: {event.src_path}, removing old chunks.")
            self.remove_file_chunks(event.src_path)

    def remove_file_chunks(self, filepath):
        existing_results = self.collection.get(limit=9999)
        if existing_results and "ids" in existing_results and existing_results["ids"]:  # Fixed typo: 'existing' → 'existing_results'
            matched_ids = []
            for doc_id in existing_results["ids"]:
                if doc_id.startswith(f"{filepath}::chunk_"):
                    matched_ids.append(doc_id)
            if matched_ids:
                self.collection.delete(ids=matched_ids)
                print(f"   🔸 Removed {len(matched_ids)} old chunk(s) for deleted/renamed file: {filepath}")

    def _handle_change(self, filepath):
        with self._lock:
            self._pending_changes[filepath] = time.time()
        threading.Thread(target=self._debounce_and_index, args=(filepath,)).start()

    def _debounce_and_index(self, filepath):
        time.sleep(DEBOUNCE_SECONDS)
        with self._lock:
            last_t = self._pending_changes.get(filepath, None)
            if not last_t:
                return
            if (time.time() - last_t) >= DEBOUNCE_SECONDS:
                self._pending_changes.pop(filepath, None)
            else:
                return

        print(f"\n🔄 Debounced re-index for file: {filepath}")
        reindex_single_file(filepath, self.collection, self.embed_model)

def watch_for_changes():
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' for watchers...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    event_handler = CodebaseEventHandler(collection, embed_model)
    observer = watchdog.observers.Observer()

    for root_dir in ROOT_DIRS:
        if os.path.exists(root_dir):
            observer.schedule(event_handler, path=root_dir, recursive=True)
            print(f"👀 Watching {root_dir} for changes...")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Index codebase + watchers + line-based chunking.")
    parser.add_argument("--watch", action="store_true", help="Watch for file changes in real time.")
    args = parser.parse_args()

    if args.watch:
        watch_for_changes()
    else:
        index_codebase()
---

# 📂 scripts/initialize_chroma.py

import chromadb

# Initialize ChromaDB in WSL-compatible path
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

# Production (main) collections
prod_collections = {
    "blueprints": "Stores AI project blueprints and recursive blueprint revisions.",
    "debugging_logs": "Logs AI debugging sessions, fixes, and error resolutions.",
    "debugging_strategies": "Stores success/failure rates for each snippet and error_type.",
    "execution_logs": "Tracks AI task execution history and outcomes.",
    "work_sessions": "Stores AI work sessions, timestamps, and activity logs.",
    "knowledge_base": "General AI memory storage (guidelines, best practices, key learnings).",
    "blueprint_versions": "Stores version docs for each blueprint.",
    "blueprint_revisions": "Holds blueprint revision proposals/triggers.",
    "project_codebase": "Indexed codebase for aggregator searching."
}

# Test collections (for running with mock data or during test scripts)
test_collections = {
    "blueprints_test": "Test collection for blueprint documents or meltdown triggers, etc.",
    "debugging_logs_test": "Test collection for debug logs with mock data.",
    "debugging_strategies_test": "Stores success/failure rates for each snippet and error_type.",
    "execution_logs_test": "Test collection for blueprint execution logs (mock).",
    "work_sessions_test": "Test collection for AI work sessions in test context.",
    "knowledge_base_test": "Test collection for knowledge docs used in testing.",
    "blueprint_versions_test": "Test collection for blueprint versions (multiple docs).",
    "blueprint_revisions_test": "Test collection for blueprint revision proposals (test).",
    "project_codebase_test": "Test indexing aggregator usage on mock code."
}

def create_collections(collection_dict):
    """
    Creates or retrieves each collection in the given dictionary.
    Prints a confirmation line for each.
    """
    for name, description in collection_dict.items():
        collection = chroma_client.get_or_create_collection(name=name)
        print(f"✅ Collection '{name}' initialized: {description}")

if __name__ == "__main__":
    print("=== Initializing Production Collections ===")
    create_collections(prod_collections)

    print("\n=== Initializing Test Collections ===")
    create_collections(test_collections)

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
debugging_strategies = chroma_client.get_or_create_collection(name="debugging_strategies")

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

# 📂 scripts/retrieve_codebase.py

#!/usr/bin/env python3
"""
retrieve_codebase.py

Performs either:
  - EMBEDDING-BASED semantic search (default)
  - (Optional) naive substring search if '--naive' is passed

Usage:
   python3 retrieve_codebase.py "division error" [n_results] [--naive]

Examples:
   python3 retrieve_codebase.py "division error" 5
   python3 retrieve_codebase.py "magic_substring" 10 --naive

One script to unify both approaches, retiring the old query_codebase_chunks.py.
"""

import sys
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"


def naive_substring_search(docs, query):
    """
    Basic substring search over chunk text.
    Return a list of (doc_text, meta, doc_id).
    """
    results = []
    for i, doc_text in enumerate(docs["documents"]):
        if query.lower() in doc_text.lower():
            meta = docs["metadatas"][i]
            doc_id = docs["ids"][i]
            results.append((doc_text, meta, doc_id))
    return results

def embedding_search(collection, query, n_results=3):
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = emb.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    matched = []
    if results and "documents" in results:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        ids = results["ids"][0]
        for doc, meta, _id in zip(docs, metas, ids):
            matched.append((doc, meta, _id))
    return matched

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 retrieve_codebase.py <query> [n_results] [--naive]")
        sys.exit(1)

    # Parse arguments
    query = args[0]
    n_results = 3
    naive_mode = False
    if len(args) > 1:
        # Check if second arg is numeric or '--naive'
        if args[1].isdigit():
            n_results = int(args[1])
            if len(args) > 2 and args[2] == "--naive":
                naive_mode = True
        else:
            if args[1] == "--naive":
                naive_mode = True
            else:
                print("Unrecognized argument, ignoring or handle it differently.")
    # If there's a third arg and it's '--naive', handle that too
    if len(args) > 2 and args[2] == "--naive":
        naive_mode = True

    # Connect to Chroma
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    if naive_mode:
        # naive substring approach => get all docs, do substring search
        all_docs = collection.get(limit=9999)
        if not all_docs or "documents" not in all_docs or not all_docs["documents"]:
            print(f"No docs found in '{COLLECTION_NAME}'.")
            sys.exit(0)

        results = naive_substring_search(all_docs, query)
        if not results:
            print(f"No matches found for substring: '{query}'")
            sys.exit(0)

        # Print top `n_results` results
        results = results[:n_results]
        print(f"\n🔹 Found {len(results)} matches for substring '{query}':\n")
        for (doc_text, meta, doc_id) in results:
            snippet = doc_text[:300] + ("..." if len(doc_text) > 300 else "")
            print(f"Doc ID: {doc_id}")
            print(f"Rel path: {meta.get('rel_path','??')}")
            print(f"Chunk index: {meta.get('chunk_index','??')}")
            print(f"Snippet: {snippet}")
            print("-"*50)

    else:
        # embedding-based approach
        matched = embedding_search(collection, query, n_results=n_results)
        if not matched:
            print(f"No semantic matches found for '{query}'")
            sys.exit(0)

        print(f"\n🔍 Found {len(matched)} semantic matches for: '{query}'\n")
        for doc_text, meta, doc_id in matched:
            snippet = doc_text[:400] + ("..." if len(doc_text) > 400 else "")
            print(f"Doc ID: {doc_id}")
            print(f"Filepath: {meta.get('filepath','??')}")
            print(f"Rel path: {meta.get('rel_path','??')}")
            print(f"Chunk #:  {meta.get('chunk_index','??')}")
            print(f"Last mod: {meta.get('mod_time','??')}")
            print()
            print("Snippet Content (first 400 chars):")
            print(snippet)
            print("=================================================\n")


if __name__ == "__main__":
    main()

---

# 📂 scripts/run_all_tests.py

#!/usr/bin/env python3
"""
run_all_tests.py

A small script that:
1) Runs pytest to discover & execute all tests in /tests/
2) Outputs a JUnit XML file for post-analysis
3) Stores a summary of results in Chroma under a "test_runs" collection (optional)
"""

import os
import subprocess
import datetime
import xml.etree.ElementTree as ET
import chromadb

def run_pytest_and_store_results():
    # 1) Ensure "results" dir for the xml, or store it in /logs/test_results
    results_dir = os.path.join("results")
    os.makedirs(results_dir, exist_ok=True)
    
    junit_xml_path = os.path.join(results_dir, "junit_report.xml")

    # 2) Run pytest with JUnit XML output
    #    We pass --junitxml=... to produce a JUnit-style XML
    print("Running Pytest on /tests/ folder...")
    cmd = [
        "pytest",
        "tests/",           # your tests folder
        "-v",               # verbose
        f"--junitxml={junit_xml_path}",
        "--maxfail=1"       # optional, to stop on first fail
    ]
    
    # run the test process
    completed = subprocess.run(cmd, capture_output=True, text=True)
    # We'll print the standard output in real time or afterwards
    print(completed.stdout)
    # If an error occurred, we want to see it
    if completed.returncode != 0:
        print("Some tests FAILED. Return code:", completed.returncode)
    else:
        print("All tests PASSED successfully!")
    
    # 3) Parse the JUnit XML to get some summary data
    if not os.path.exists(junit_xml_path):
        print("No JUnit XML found. Possibly Pytest never ran or a path issue.")
        return

    tree = ET.parse(junit_xml_path)
    root = tree.getroot()

    # Typically, root = <testsuites> with <testsuite> children in JUnit XML
    # We'll gather some high-level stats
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    for testsuite in root.findall("testsuite"):
        total_tests += int(testsuite.get("tests", 0))
        total_failures += int(testsuite.get("failures", 0))
        total_errors += int(testsuite.get("errors", 0))
        total_skipped += int(testsuite.get("skipped", 0))

    # Just for a quick summary
    print(f"JUnit Summary: tests={total_tests}, failures={total_failures}, errors={total_errors}, skipped={total_skipped}")

    # 4) Optionally store the summary in Chroma "test_runs" collection
    #    We'll embed or store the entire XML or just the stats + log
    client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
    test_runs_collection = client.get_or_create_collection("test_runs")  # rename as you like

    # We'll create a doc id with a timestamp for uniqueness
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    doc_id = f"test_run_{timestamp_str}"

    # Minimal JSON to store
    test_run_data = {
        "timestamp": timestamp_str,
        "tests": total_tests,
        "failures": total_failures,
        "errors": total_errors,
        "skipped": total_skipped,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        # You can also embed the full JUnit XML as a string if desired:
        # "junit_xml": open(junit_xml_path, "r").read(),
    }

    try:
        test_runs_collection.add(
            ids=[doc_id],
            documents=[str(test_run_data)],  # store JSON as string
            metadatas=[test_run_data]        # partial duplication, or pick a subset
        )
        print(f"Stored test run results in Chroma under doc_id={doc_id}")
    except Exception as e:
        print("Failed to store test results in Chroma:", e)

def main():
    run_pytest_and_store_results()

if __name__ == "__main__":
    main()

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
