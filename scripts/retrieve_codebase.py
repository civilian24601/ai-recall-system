#!/usr/bin/env python3
"""
retrieve_codebase.py

Performs either:
  - EMBEDDING-BASED semantic search (default)
  - (Optional) naive substring search if '--naive' is passed

Usage:
   python3 retrieve_codebase.py "division error" [n_results] [--naive]

Examples:
   python3 retrieve_codebase.py "division error" 5
   python3 retrieve_codebase.py "magic_substring" 10 --naive

One script to unify both approaches, retiring the old query_codebase_chunks.py.
"""

import sys
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"  # Collection name in ChromaDB

def naive_substring_search(docs, query):
    """
    Basic substring search over chunk text.
    Return a list of (doc_text, meta, doc_id).
    """
    results = []
    for i, doc_text in enumerate(docs["documents"]):
        if query.lower() in doc_text.lower():
            meta = docs["metadatas"][i]
            doc_id = docs["ids"][i]
            results.append((doc_text, meta, doc_id))
    return results

def embedding_search(collection, query, n_results=3):
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = emb.embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    matched = []
    if results and "documents" in results:
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        ids = results["ids"][0]
        for doc, meta, _id in zip(docs, metas, ids):
            matched.append((doc, meta, _id))
    return matched

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python3 retrieve_codebase.py <query> [n_results] [--naive]")
        sys.exit(1)

    # Parse arguments
    query = args[0]
    n_results = 3
    naive_mode = False
    if len(args) > 1:
        if args[1].isdigit():
            n_results = int(args[1])
            if len(args) > 2 and args[2] == "--naive":
                naive_mode = True
        else:
            if args[1] == "--naive":
                naive_mode = True
            else:
                print("Unrecognized argument, ignoring or handle it differently.")
    if len(args) > 2 and args[2] == "--naive":
        naive_mode = True

    # Connect to Chroma
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    if naive_mode:
        # Naive substring approach => get all docs, do substring search
        all_docs = collection.get(limit=9999)
        if not all_docs or "documents" not in all_docs or not all_docs["documents"]:
            print(f"No docs found in '{COLLECTION_NAME}'.")
            sys.exit(0)

        results = naive_substring_search(all_docs, query)
        if not results:
            print(f"No matches found for substring: '{query}'")
            sys.exit(0)

        # Print top `n_results` results
        results = results[:n_results]
        print(f"\n🔹 Found {len(results)} matches for substring '{query}':\n")
        for (doc_text, meta, doc_id) in results:
            snippet = doc_text[:300] + ("..." if len(doc_text) > 300 else "")
            print(f"Doc ID: {doc_id}")
            print(f"Rel path: {meta.get('rel_path', meta.get('filename', '??'))}")  # Fallback to filename
            print(f"Chunk index: {meta.get('chunk_index', '??')}")
            print(f"Snippet: {snippet}")
            print("-"*50)

    else:
        # Embedding-based approach
        matched = embedding_search(collection, query, n_results=n_results)
        if not matched:
            print(f"No semantic matches found for '{query}'")
            sys.exit(0)

        print(f"\n🔍 Found {len(matched)} semantic matches for: '{query}'\n")
        for doc_text, meta, doc_id in matched:
            snippet = doc_text[:400] + ("..." if len(doc_text) > 400 else "")
            # Adjusted to handle both project_codebase and knowledge_base metadata
            filepath = meta.get('filepath', meta.get('filename', '??'))  # Fallback to filename
            rel_path = meta.get('rel_path', meta.get('filename', '??'))  # Fallback to filename
            chunk_num = meta.get('chunk_index', meta.get('chunk', '??'))  # Fallback to chunk
            last_mod = meta.get('mod_time', meta.get('mtime', '??'))     # Fallback to mtime
            print(f"Doc ID: {doc_id}")
            print(f"Filepath: {filepath}")
            print(f"Rel path: {rel_path}")
            print(f"Chunk #:  {chunk_num}")
            print(f"Last mod: {last_mod}")
            print()
            print("Snippet Content (first 400 chars):")
            print(snippet)
            print("=================================================\n")

if __name__ == "__main__":
    main()