import chromadb
import os

def store_markdown_in_chroma():
    """Indexes refined markdown logs into ChromaDB for AI recall."""
    chroma_client = chromadb.PersistentClient(path="chroma_db/")
    collection = chroma_client.get_or_create_collection("markdown_logs")

    log_dirs = ["logs/", "knowledge_base/"]
    for log_dir in log_dirs:
        for filename in os.listdir(log_dir):
            if filename.endswith(".md"):
                with open(os.path.join(log_dir, filename), "r") as f:
                    text_content = f.read()
                    collection.add(
                        documents=[text_content],
                        metadatas=[{"filename": filename}],
                        ids=[filename]
                    )

    print(f"✅ All markdown logs indexed in ChromaDB!")

# Example usage
store_markdown_in_chroma()
