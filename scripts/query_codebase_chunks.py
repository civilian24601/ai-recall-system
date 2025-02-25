#!/usr/bin/env python3
"""
query_codebase_chunks.py

Simple retrieval from the "project_codebase" ChromaDB collection
based on naive substring matching or metadata filtering.

If you want semantic search, you can replace with an embedding-based approach
using e.g. langchain or chroma client embedding queries.
"""

import sys
import os
import json
import chromadb

# Where is the project root
PROJECT_ROOT = "/mnt/f/projects/ai-recall-system"
CHROMA_DB_PATH = os.path.join(PROJECT_ROOT, "chroma_db")
COLLECTION_NAME = "project_codebase"

def naive_substring_search(docs, query):
    """
    Basic substring search over chunk text.
    If you want vector similarity, switch to an embedding query.
    """
    results = []
    for i, doc_text in enumerate(docs["documents"]):
        if query.lower() in doc_text.lower():
            meta = docs["metadatas"][i]
            doc_id = docs["ids"][i]
            results.append({
                "doc_id": doc_id,
                "relative_path": meta["relative_path"],
                "chunk_index": meta["chunk_index"],
                "file_type": meta["file_type"],
                "snippet": doc_text[:300] + ("..." if len(doc_text) > 300 else "")
            })
    return results

def main():
    if len(sys.argv) < 2:
        print("Usage: python query_codebase_chunks.py \"search term\"")
        sys.exit(1)

    query = sys.argv[1]
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    # For demo, we just fetch all docs (limit=9999) and do naive substring search
    # In a big codebase, this is NOT efficient. We can do real embeddings or chunk filtering.
    results = collection.get(limit=9999)

    if not results or "documents" not in results or not results["documents"]:
        print(f"No codebase chunks found in collection '{COLLECTION_NAME}'.")
        return

    # naive substring search
    matched = naive_substring_search(results, query)
    if not matched:
        print(f"No matches for query: '{query}'")
        return

    print(f"\n🔹 Found {len(matched)} matches for '{query}':\n")
    for m in matched[:10]:  # show first 10
        print(f"Doc ID: {m['doc_id']}")
        print(f"Path: {m['relative_path']}")
        print(f"Type: {m['file_type']}")
        print(f"Snippet: {m['snippet']}\n{'-'*60}")

if __name__ == "__main__":
    main()
