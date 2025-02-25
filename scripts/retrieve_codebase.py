#!/usr/bin/env python3
"""
retrieve_codebase.py

Queries your 'project_codebase' collection in ChromaDB to find relevant code/doc
chunks using embeddings. This aligns with the new index_codebase.py approach
(word-based or line-based chunking, stable doc_ids, hashed chunks, etc.).

Usage:
   python3 retrieve_codebase.py "division error" 5

Which will retrieve the top 5 matching chunks for "division error".
"""

import sys
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"

def retrieve_code_snippets(query: str, n_results: int = 3):
    """
    Performs an embedding-based semantic search over 'project_codebase' in Chroma.
    Returns a list of (doc_content, metadata) tuples.
    """
    # 1) Connect to Chroma
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # 2) Load embeddings model (same as used when indexing)
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = emb.embed_query(query)

    # 3) Query the collection by embedding
    #    This uses semantic similarity to find relevant chunks
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    matched_chunks = []
    if results and "documents" in results:
        # Typically results["documents"] is a list of lists
        # We'll iterate the top-level list => results["documents"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        for doc, meta in zip(docs, metas):
            matched_chunks.append((doc, meta))

    return matched_chunks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 retrieve_codebase.py <query> [n_results]")
        sys.exit(1)

    query_text = sys.argv[1]
    n = 3
    if len(sys.argv) > 2:
        n = int(sys.argv[2])

    snippets = retrieve_code_snippets(query_text, n_results=n)

    print(f"\n🔍 Found {len(snippets)} relevant chunks for: '{query_text}'\n")
    for i, (doc, meta) in enumerate(snippets, start=1):
        filepath = meta.get("filepath", "??")
        rel_path = meta.get("rel_path", "??")
        chunk_idx = meta.get("chunk_index", "??")
        mod_time = meta.get("mod_time", "??")
        print(f"Result #{i}")
        print("-------------------------------------------------")
        print(f"Filepath: {filepath}")
        print(f"Rel path: {rel_path}")
        print(f"Chunk #:  {chunk_idx}")
        print(f"Last mod: {mod_time}")
        print()
        print("Snippet Content (first 400 chars):")
        print(doc[:400] + ("..." if len(doc) > 400 else ""))
        print("=================================================\n")
