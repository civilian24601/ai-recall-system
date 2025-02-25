import chromadb

def check_doc_count(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db", collection_name="project_codebase"):
    client = chromadb.PersistentClient(path=chroma_path)
    coll = client.get_collection(collection_name)
    data = coll.get()
    print(f"Found {len(data['documents'])} docs in '{collection_name}'")

if __name__ == "__main__":
    check_doc_count()
