import chromadb

# Initialize ChromaDB in WSL-compatible path
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

# Production (main) collections
prod_collections = {
    "blueprints": "Stores AI project blueprints and recursive blueprint revisions.",
    "debugging_logs": "Logs AI debugging sessions, fixes, and error resolutions.",
    "debugging_strategies": "Stores success/failure rates for each snippet and error_type.",
    "execution_logs": "Tracks AI task execution history and outcomes.",
    "work_sessions": "Stores AI work sessions, timestamps, and activity logs.",
    "knowledge_base": "General AI memory storage (guidelines, best practices, key learnings).",
    "blueprint_versions": "Stores version docs for each blueprint.",
    "blueprint_revisions": "Holds blueprint revision proposals/triggers.",
    "project_codebase": "Indexed codebase for aggregator searching."
}

# Test collections (for running with mock data or during test scripts)
test_collections = {
    "blueprints_test": "Test collection for blueprint documents or meltdown triggers, etc.",
    "debugging_logs_test": "Test collection for debug logs with mock data.",
    "debugging_strategies_test": "Stores success/failure rates for each snippet and error_type.",
    "execution_logs_test": "Test collection for blueprint execution logs (mock).",
    "work_sessions_test": "Test collection for AI work sessions in test context.",
    "knowledge_base_test": "Test collection for knowledge docs used in testing.",
    "blueprint_versions_test": "Test collection for blueprint versions (multiple docs).",
    "blueprint_revisions_test": "Test collection for blueprint revision proposals (test).",
    "project_codebase_test": "Test indexing aggregator usage on mock code."
}

def create_collections(collection_dict):
    """
    Creates or retrieves each collection in the given dictionary.
    Prints a confirmation line for each.
    """
    for name, description in collection_dict.items():
        collection = chroma_client.get_or_create_collection(name=name)
        print(f"✅ Collection '{name}' initialized: {description}")

if __name__ == "__main__":
    print("=== Initializing Production Collections ===")
    create_collections(prod_collections)

    print("\n=== Initializing Test Collections ===")
    create_collections(test_collections)
