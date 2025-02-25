import chromadb

# Initialize ChromaDB in the WSL filesystem
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

print("✅ ChromaDB is running inside WSL and ready for AI queries!")
