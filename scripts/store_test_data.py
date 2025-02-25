import chromadb
import json

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

# Define test data
test_data = {
    "blueprints": {
        "id": "blueprint_001",
        "name": "AI Debugging Strategy v1",
        "version": "1.0",
        "description": "Defines AI debugging recall process."
    },
    "debugging_logs": {
        "id": "debug_001",
        "timestamp": "2025-02-14T12:30:00",
        "error_message": "SQL Integrity Constraint Violation",
        "fix_attempted": "Added unique constraint to schema."
    },
    "execution_logs": {
        "id": "execution_001",
        "task": "Retrieve debugging logs",
        "timestamp": "2025-02-14T13:00:00",
        "execution_success": True,
        "duration": 1.2
    },
    "work_sessions": {
        "id": "session_001",
        "session_name": "AI Work Session 1",
        "start_time": "2025-02-14T10:00:00",
        "end_time": "2025-02-14T12:00:00",
        "tasks_completed": ["Blueprint Retrieval", "ChromaDB Initialization"]
    },
    "knowledge_base": {
        "id": "kb_001",
        "category": "Coding Best Practices",
        "content": "Always use snake_case for function names in Python.",
        "last_updated": "2025-02-14T11:45:00"
    }
}

# Overwrite old collections to prevent duplicates
for collection_name in test_data.keys():
    chroma_client.delete_collection(name=collection_name)  # Force delete bad data
    collection = chroma_client.get_or_create_collection(name=collection_name)

    # Convert dictionary to proper JSON before storing
    json_document = json.dumps(test_data[collection_name], ensure_ascii=False)
    
    print(f"📌 Storing in {collection_name}: {json_document}")  # Verify correct format
    collection.add(ids=[test_data[collection_name]["id"]], documents=[json_document])

print("✅ Test data stored successfully in ChromaDB with proper JSON formatting!")
