import chromadb

# Initialize ChromaDB in WSL-compatible path
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

# Define collections
collections = {
    "blueprints": "Stores AI project blueprints and recursive blueprint revisions.",
    "debugging_logs": "Logs AI debugging sessions, fixes, and error resolutions.",
    "execution_logs": "Tracks AI task execution history and outcomes.",
    "work_sessions": "Stores AI work sessions, timestamps, and activity logs.",
    "knowledge_base": "General AI memory storage (guidelines, best practices, key learnings)."
}

# Create collections if they don’t exist
for name, description in collections.items():
    collection = chroma_client.get_or_create_collection(name=name)
    print(f"✅ Collection '{name}' initialized: {description}")
