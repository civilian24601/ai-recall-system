# /scripts/inspect_collections.py
#!/usr/bin/env python3
"""
inspect_collections.py

Inspects and prints an overview of collections and their contents in ChromaDB.
"""

import chromadb

def inspect_collections(chroma_path="/mnt/f/projects/ai-recall-system/chroma_db"):
    client = chromadb.PersistentClient(path=chroma_path)
    
    all_coll = client.list_collections()
    for coll_name in all_coll:
        coll = client.get_collection(coll_name)
        # Query some stats. If you just call coll.get() with no filter, you can see how many docs we have.
        data = coll.get()
        doc_count = len(data["documents"])
        print(f"Collection: {coll_name} => {doc_count} documents")

if __name__ == "__main__":
    inspect_collections()