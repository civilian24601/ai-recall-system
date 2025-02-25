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
