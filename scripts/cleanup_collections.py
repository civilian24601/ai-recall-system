# /scripts/cleanup_collections.py
#!/usr/bin/env python3
"""
cleanup_collections.py

Wipes all collections in ChromaDB to start fresh, excluding none.
"""

import chromadb

def wipe_all_collections(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db"):
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Print existing collections for reference
    collections = client.list_collections()
    print("🔎 Current collections in Chroma before wiping:")
    for c in collections:
        print(f" - {c}")

    # Delete all collections
    for collection_name in collections:
        try:
            client.delete_collection(collection_name)
            print(f"✅ Wiped collection '{collection_name}'")
        except Exception as e:
            print(f"❌ Could not wipe '{collection_name}': {e}")

    # Re-list collections after wiping
    print("\n🔎 Collections after wiping (should be empty):")
    collections_after = client.list_collections()
    for c in collections_after:
        print(f" - {c}")

if __name__ == "__main__":
    wipe_all_collections()