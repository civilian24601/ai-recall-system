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