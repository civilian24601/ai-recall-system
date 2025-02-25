#!/usr/bin/env python3
"""
aggregator_search.py

A "Memory Palace" style aggregator that queries multiple Chroma collections
(knowledge_base, work_sessions, blueprints, blueprint_revisions, execution_logs,
debugging_logs, project_codebase, blueprint_versions) in one shot, using a
384-dim embedding model name so it doesn't mismatch your environment.

Usage:
    python3 aggregator_search.py "division error" [5]
"""

import sys
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

CHROMA_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"

COLLECTIONS_TO_QUERY = [
    "knowledge_base",
    "work_sessions",
    "blueprints",
    "blueprint_revisions",
    "execution_logs",
    "debugging_logs",
    "project_codebase",
    "blueprint_versions",
]

def aggregator_search(query: str, top_n: int = 3):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    q_embed = emb_model.embed_query(query)
    combined_results = []

    for coll_name in COLLECTIONS_TO_QUERY:
        try:
            coll = client.get_or_create_collection(coll_name)
        except Exception as e:
            print(f"⚠ Could not access collection '{coll_name}': {e}")
            continue

        try:
            # get top_n from this domain
            res = coll.query(query_embeddings=[q_embed], n_results=top_n)
        except Exception as e:
            print(f"⚠ Error querying '{coll_name}': {e}")
            continue

        if not res or "documents" not in res or len(res["documents"]) == 0:
            continue

        docs = res["documents"][0]
        metas = res["metadatas"][0] if "metadatas" in res else [{}]*len(docs)
        dists = res.get("distances", [[]])
        if len(dists) > 0 and len(dists[0]) == len(docs):
            dists = dists[0]
        else:
            dists = [9999.0]*len(docs)

        for doc, meta, dist in zip(docs, metas, dists):
            combined_results.append({
                "collection": coll_name,
                "distance": dist,
                "document": doc,
                "metadata": meta
            })

    combined_results.sort(key=lambda x: x["distance"])
    return combined_results[:top_n]

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 aggregator_search.py <query> [n_results]")
        sys.exit(1)

    query_text = sys.argv[1]
    n = 3
    if len(sys.argv) > 2:
        n = int(sys.argv[2])

    results = aggregator_search(query_text, n)

    print(f"\n🔎 Combined aggregator search for: '{query_text}' (top {n} overall)\n")
    for i, r in enumerate(results, start=1):
        c_name = r["collection"]
        dist = r["distance"]
        doc = r["document"]
        meta = r["metadata"] or {}  # safe fallback

        print(f"Result #{i} | Collection: {c_name} | Distance: {dist}")
        print("-------------------------------------------------")
        if not isinstance(meta, dict):
            meta = {}
        for k, v in meta.items():
            print(f"{k}: {v}")

        snippet = doc[:400]
        snippet += "..." if len(doc) > 400 else ""
        print("\nSnippet Preview:")
        print(snippet)
        print("=================================================\n")

if __name__ == "__main__":
    main()
