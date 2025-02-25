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
