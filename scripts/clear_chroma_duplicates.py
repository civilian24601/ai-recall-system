import chromadb
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Chroma client
chroma_client = chromadb.PersistentClient(
    path="/mnt/f/projects/ai-recall-system/chroma_db/"
)
debugging_logs_collection = chroma_client.get_or_create_collection(name="debugging_logs")

def clear_duplicates():
    """Clear duplicate entries from the ChromaDB collection."""
    logging.info("Retrieving all entries from ChromaDB collection...")
    all_entries = debugging_logs_collection.get()

    if not all_entries or "documents" not in all_entries:
        logging.info("No entries found in ChromaDB collection.")
        return

    documents = all_entries["documents"]
    ids = all_entries["ids"]
    unique_ids = set()
    duplicates = []

    for doc_id, doc in zip(ids, documents):
        if doc_id in unique_ids:
            duplicates.append(doc_id)
        else:
            unique_ids.add(doc_id)

    if not duplicates:
        logging.info("No duplicate entries found.")
        return

    logging.info(f"Found {len(duplicates)} duplicate entries. Removing duplicates...")
    debugging_logs_collection.delete(ids=duplicates)
    logging.info("Duplicates removed successfully.")

if __name__ == "__main__":
    clear_duplicates()