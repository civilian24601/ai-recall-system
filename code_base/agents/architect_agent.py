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
