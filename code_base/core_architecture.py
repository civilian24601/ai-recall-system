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
