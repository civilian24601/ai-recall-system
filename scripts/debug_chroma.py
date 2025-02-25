import chromadb

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

def dump_raw_data(collection_name):
    """Dump raw stored documents in a collection."""
    collection = chroma_client.get_or_create_collection(name=collection_name)
    results = collection.get()

    print(f"\n📌 RAW DATA IN '{collection_name}':")
    for doc in results["documents"]:
        print(f"🔹 Stored Entry: {repr(doc)}")  # Show EXACT format

if __name__ == "__main__":
    for collection in ["blueprints", "debugging_logs", "execution_logs", "work_sessions", "knowledge_base"]:
        dump_raw_data(collection)
