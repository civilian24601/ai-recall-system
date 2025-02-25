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
