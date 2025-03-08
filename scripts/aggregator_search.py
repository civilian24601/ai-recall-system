#!/usr/bin/env python3
"""
aggregator_search.py (Advanced with dedup)

We unify embedding + naive results in "both" mode, but we deduplicate if the
same doc_id / same collection is found from both approaches, picking the one
with the lower distance so the doc appears only once in final output.

Usage:
   python aggregator_search.py "division error" [top_n] [--mode naive|both|guidelines_code]
"""

import sys
import chromadb
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

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
    logger.debug(f"Naive search in {coll_name} found {len(results)} matches for query '{query}'")
    return results

def aggregator_search(query, top_n=3, mode="embedding"):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    combined_map = {}  # key=(collection, doc_id), value= best record
    fetch_count = top_n * 3 if mode in ("embedding", "both", "guidelines_code") else 0

    if mode in ("embedding", "both", "guidelines_code"):
        query_embed = emb_model.embed_query(query)
        logger.debug(f"Embedded query '{query}' with shape {len(query_embed)}")

    for coll_name in COLLECTIONS_TO_QUERY:
        try:
            coll = client.get_or_create_collection(coll_name)
        except Exception as e:
            logger.error(f"Could not access collection '{coll_name}': {e}")
            continue

        if mode in ("embedding", "both", "guidelines_code"):
            try:
                res = coll.query(query_embeddings=[query_embed], n_results=fetch_count)
            except Exception as e:
                logger.error(f"Error (embedding) in '{coll_name}': {e}")
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
                    # Stronger boost for ai_coding_guidelines.md
                    if meta.get("filename") == "ai_coding_guidelines.md":
                        dist = max(0, dist - 1.0)  # Significant boost
                    elif meta.get("filename", "").endswith(".md") or meta.get("guideline", False):
                        dist = max(0, dist - 0.7)  # Moderate boost for other markdown
                    # Force naive-only docs to rank via substring
                    if meta.get("naive_only", False) and dist < 9.0:
                        dist = 9.0
                    key = (coll_name, doc_id)
                    if key not in combined_map or dist < combined_map[key]["distance"]:
                        combined_map[key] = {
                            "collection": coll_name,
                            "doc_id": doc_id,
                            "distance": dist,
                            "document": doc_text,
                            "metadata": meta
                        }
                logger.debug(f"Embedding search in {coll_name} added {len([k for k in combined_map.keys() if k[0] == coll_name])} unique docs")

        if mode in ("naive", "both"):
            try:
                naive_docs = coll.get(limit=9999)
            except Exception as e:
                logger.error(f"Error (naive get) in '{coll_name}': {e}")
                naive_docs = None

            if naive_docs and "documents" in naive_docs and naive_docs["documents"]:
                naive_results = naive_substring_search(naive_docs, query, coll_name)
                for r in naive_results:
                    key = (r["collection"], r["doc_id"])
                    if key not in combined_map or r["distance"] < combined_map[key]["distance"]:
                        combined_map[key] = r
                logger.debug(f"Naive search in {coll_name} added {len([k for k in combined_map.keys() if k[0] == coll_name])} unique docs")

    combined_list = list(combined_map.values())
    combined_list.sort(key=lambda x: x["distance"])

    # Filter for guidelines_code mode
    if mode == "guidelines_code":
        combined_list = [r for r in combined_list if 
                        (r["metadata"].get("filename", "").endswith(".md") or 
                         r["metadata"].get("filename", "").endswith(".py"))]
        logger.debug(f"Filtered to {len(combined_list)} guidelines/code docs for mode 'guidelines_code'")

    # Ensure ai_coding_guidelines.md is included if available
    if mode == "guidelines_code" and combined_list:
        for r in combined_list:
            if r["metadata"].get("filename") == "ai_coding_guidelines.md":
                logger.debug(f"Ensuring ai_coding_guidelines.md inclusion")
                break
        else:
            # If not found, prioritize any guideline
            for r in combined_list:
                if r["metadata"].get("filename", "").endswith(".md"):
                    logger.debug(f"Ensuring guideline inclusion, added {r['metadata'].get('filename')}")
                    break

    return combined_list[:top_n]

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python aggregator_search.py <query> [top_n] [--mode naive|both|guidelines_code]")
        sys.exit(1)

    query_text = args[0]
    top_n = 3
    mode = "embedding"  # default

    if len(args) > 1:
        if args[1].isdigit():
            top_n = int(args[1])
        elif args[1].startswith("--mode"):
            pass
        else:
            if args[1] in ("naive", "both", "guidelines_code"):
                mode = args[1]

    if "--mode" in args:
        idx = args.index("--mode")
        if idx + 1 < len(args):
            possible_mode = args[idx + 1]
            if possible_mode in ("naive", "both", "guidelines_code"):
                mode = possible_mode

    results = aggregator_search(query_text, top_n, mode)

    print(f"\n🔎 aggregator_search for: '{query_text}' (mode={mode}, top {top_n} overall)\n")
    for i, r in enumerate(results, start=1):
        c_name = r["collection"]
        dist = r["distance"]
        doc = r["document"]
        meta = r["metadata"] or {}
        doc_id = r["doc_id"]

        dist_str = f"{dist:.4f}" if dist < 9.0 else f"(subRank~{int(dist-9)})"
        print(f"Result #{i} | Collection: {c_name} | doc_id: {doc_id} | distance: {dist_str}")
        print("-------------------------------------------------")
        for k, v in meta.items():
            print(f"{k}: {v}")
        snippet = doc[:300]
        if len(doc) > 300:
            snippet += "..."
        print("\nSnippet Preview:")
        print(snippet)
        print("=================================================\n")

if __name__ == "__main__":
    main()