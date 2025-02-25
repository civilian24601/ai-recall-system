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
