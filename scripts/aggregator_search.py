#!/usr/bin/env python3
"""
aggregator_search.py (Advanced with dedup)

We unify embedding + naive results in "both" mode, but we deduplicate if the
same doc_id / same collection is found from both approaches, picking the one
with the lower distance so the doc appears only once in final output.

Usage:
   python aggregator_search.py "division error" [top_n] [--mode naive|both]
"""

import sys
import chromadb
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
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

def naive_substring_search(docs_dict, query, coll_name):
    """
    Return list of:
       {"collection": coll_name, "distance": 9.0 + rank, "document": doc_text, "metadata": meta, "doc_id": <the doc id>}
    """
    results = []
    all_docs = docs_dict["documents"]
    all_metas = docs_dict["metadatas"]
    all_ids = docs_dict["ids"]
    query_lower = query.lower()

    rank = 0
    for doc_text, meta, doc_id in zip(all_docs, all_metas, all_ids):
        if query_lower in doc_text.lower():
            # We'll do pseudo-dist = 9 + rank
            distance = 9.0 + rank
            if not isinstance(meta, dict):
                meta = {}
            results.append({
                "collection": coll_name,
                "doc_id": doc_id,
                "distance": distance,
                "document": doc_text,
                "metadata": meta
            })
            rank += 1
    return results

def aggregator_search(query, top_n=3, mode="embedding"):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # We'll store final results in "combined_results" but also deduplicate by (collection, doc_id).
    combined_map = {}  # key=(collection, doc_id), value= best record

    # We fetch top_n * 3 from each collection if embedding is used:
    fetch_count = top_n * 3 if mode in ("embedding", "both") else 0

    if mode in ("embedding", "both"):
        # We'll embed once:
        query_embed = emb_model.embed_query(query)

    for coll_name in COLLECTIONS_TO_QUERY:
        try:
            coll = client.get_or_create_collection(coll_name)
        except Exception as e:
            print(f"⚠ Could not access collection '{coll_name}': {e}")
            continue

        # A) Embedding approach
        if mode in ("embedding", "both"):
            try:
                res = coll.query(query_embeddings=[query_embed], n_results=fetch_count)
            except Exception as e:
                print(f"⚠ Error (embedding) in '{coll_name}': {e}")
                res = None

            if res and "documents" in res and res["documents"]:
                docs = res["documents"][0]
                metas = res["metadatas"][0] if "metadatas" in res else [{}]*len(docs)
                dists = res.get("distances", [[]])
                if dists and len(dists) > 0 and len(dists[0]) == len(docs):
                    dists = dists[0]
                else:
                    dists = [9999.0]*len(docs)

                ids = res["ids"][0] if "ids" in res else []
                for doc_text, meta, dist, doc_id in zip(docs, metas, dists, ids):
                    if not isinstance(meta, dict):
                        meta = {}
                    # Boost guideline chunks slightly in embedding results
                    if meta.get("guideline", False):
                        dist = max(0, dist - 0.1)  # Small boost, cap at 0 to avoid negative distances
                    # Force naive-only docs to stay out of embedding rankings
                    if meta.get("naive_only", False) and dist < 9.0:
                        dist = 9.0  # Ensures naive docs rank via substring only
                    key = (coll_name, doc_id)
                    # If we have a record for this key, keep the best (lowest dist)
                    if key not in combined_map or dist < combined_map[key]["distance"]:
                        combined_map[key] = {
                            "collection": coll_name,
                            "doc_id": doc_id,
                            "distance": dist,
                            "document": doc_text,
                            "metadata": meta
                        }

        # B) Naive substring approach
        if mode in ("naive", "both"):
            try:
                naive_docs = coll.get(limit=9999)
            except Exception as e:
                print(f"⚠ Error (naive get) in '{coll_name}': {e}")
                naive_docs = None

            if naive_docs and "documents" in naive_docs and naive_docs["documents"]:
                naive_results = naive_substring_search(naive_docs, query, coll_name)
                for r in naive_results:
                    key = (r["collection"], r["doc_id"])
                    # If no record or distance is bigger in combined_map, update
                    if key not in combined_map or r["distance"] < combined_map[key]["distance"]:
                        combined_map[key] = r

    # Now unify them, sort by ascending distance
    combined_list = list(combined_map.values())
    combined_list.sort(key=lambda x: x["distance"])

    # final top_n overall
    return combined_list[:top_n]

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python aggregator_search.py <query> [top_n] [--mode naive|both]")
        sys.exit(1)

    query_text = args[0]
    top_n = 3
    mode = "embedding"  # default

    # parse second arg
    if len(args) > 1:
        if args[1].isdigit():
            top_n = int(args[1])
        elif args[1].startswith("--mode"):
            pass
        else:
            if args[1] in ("naive","both"):
                mode = args[1]

    # parse optional --mode
    if "--mode" in args:
        idx = args.index("--mode")
        if idx+1 < len(args):
            possible_mode = args[idx+1]
            if possible_mode in ("naive","both"):
                mode = possible_mode

    results = aggregator_search(query_text, top_n, mode)

    print(f"\n🔎 aggregator_search for: '{query_text}' (mode={mode}, top {top_n} overall)\n")
    for i, r in enumerate(results, start=1):
        c_name = r["collection"]
        dist = r["distance"]
        doc = r["document"]
        meta = r["metadata"] or {}
        doc_id = r["doc_id"]

        # if dist>=9 => substring
        dist_str = f"{dist:.4f}"
        if dist >= 9.0:
            # e.g. substring => dist=9 + rank
            # we can do a custom marker
            dist_str = f"(subRank~{int(dist-9)})"

        print(f"Result #{i} | Collection: {c_name} | doc_id: {doc_id} | distance: {dist_str}")
        print("-------------------------------------------------")
        for k,v in meta.items():
            print(f"{k}: {v}")
        snippet = doc[:300]
        if len(doc)>300:
            snippet += "..."
        print("\nSnippet Preview:")
        print(snippet)
        print("=================================================\n")

if __name__ == "__main__":
    main()