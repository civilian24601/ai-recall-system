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
