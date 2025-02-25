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
