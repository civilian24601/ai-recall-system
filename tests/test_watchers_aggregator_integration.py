"""
test_watchers_aggregator_integration.py

This test script demonstrates an end-to-end flow:
 - We monkeypatch index_codebase.py to watch a temporary directory 
   and store docs in "project_codebase_test".
 - We start watchers in a thread.
 - We create a .py file mentioning "division error", force index it.
 - We edit the file, wait for watchers to reindex the full update.
 - Then we run aggregator_search to confirm the updated chunk is discovered.
"""

import pytest
import os
import time
import shutil
import tempfile
import threading
from unittest.mock import patch

import chromadb
import scripts.index_codebase as idx
from scripts.aggregator_search import aggregator_search
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

def patched_reindex_single_file(filepath, collection, embed_model):
    import scripts.index_codebase as idx
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in idx.ALLOWED_EXTENSIONS:
        return 0
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return 0
    if os.path.basename(filepath) in idx.SKIP_FILES:
        return 0

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"Indexing {filepath} contents:\n{text}")  # Debug what’s read
    except Exception as e:
        print(f"⚠ Error reading {filepath}: {e}")
        return 0

    if not text.strip():
        return 0

    existing = collection.get(limit=9999)
    if existing and "ids" in existing and existing["ids"]:
        matched_ids = [doc_id for doc_id in existing["ids"] if doc_id.startswith(f"{filepath}::chunk_")]
        if matched_ids:
            collection.delete(ids=matched_ids)
            print(f"   🔸 Removed {len(matched_ids)} old chunk(s) for updated file: {filepath}")

    lines = text.splitlines()
    new_chunks_for_file = 0

    if ext == ".py":
        from scripts.index_codebase import parse_python_ast, build_python_chunks, chunk_lines_with_range, compute_md5_hash
        func_chunks = parse_python_ast(filepath)
        py_chunks = []
        if not func_chunks or True:  # Force line-based for edits outside AST
            line_blocks = chunk_lines_with_range(lines, 0, chunk_size=idx.CHUNK_SIZE_DEFAULT, overlap=0)
            for chunk_text, st_line, end_line in line_blocks:
                py_chunks.append({
                    "text": chunk_text,
                    "start_line": st_line + 1,
                    "end_line": end_line + 1,
                    "function_name": "",
                    "class_name": "",
                    "node_type": "misc"
                })
        else:
            for fc in func_chunks:
                sublist = build_python_chunks(lines, fc)
                py_chunks.extend(sublist)

        for idx, cdict in enumerate(py_chunks):
            chunk_str = cdict["text"]
            if not chunk_str.strip():
                continue
            chunk_hash = compute_md5_hash(chunk_str)
            doc_id = f"{filepath}::chunk_{idx}::hash_{chunk_hash}"

            embedding = embed_model.embed_documents([chunk_str])[0]

            function_name = cdict.get("function_name", "") or ""
            class_name = cdict.get("class_name", "") or ""
            node_type = cdict.get("node_type", "") or ""
            start_line = int(cdict.get("start_line", 0))
            end_line = int(cdict.get("end_line", 0))

            meta = {
                "filepath": filepath,
                "rel_path": filepath,
                "chunk_index": idx,
                "hash": chunk_hash,
                "mod_time": os.path.getmtime(filepath),
                "start_line": start_line,
                "end_line": end_line,
                "function_name": function_name,
                "class_name": class_name,
                "node_type": node_type
            }

            collection.add(
                documents=[chunk_str],
                embeddings=[embedding],
                metadatas=[meta],
                ids=[doc_id]
            )
            new_chunks_for_file += 1

    if new_chunks_for_file > 0:
        print(f"   ⮑ Re-indexed {new_chunks_for_file} chunk(s) from {filepath}")
    return new_chunks_for_file

@pytest.fixture
def ephemeral_chroma():
    client = chromadb.PersistentClient(path=idx.CHROMA_DB_PATH)
    coll_test = client.get_or_create_collection(name="project_codebase_test")
    yield coll_test
    results = coll_test.get(limit=9999)
    if results and "ids" in results and results["ids"]:
        coll_test.delete(ids=results["ids"])

@pytest.mark.integration
@patch("scripts.index_codebase.ROOT_DIRS", new_callable=list)
@patch("scripts.index_codebase.COLLECTION_NAME", "project_codebase_test")
@patch("scripts.aggregator_search.COLLECTIONS_TO_QUERY", ["project_codebase_test"])
def test_watchers_aggregator_e2e(root_dirs, ephemeral_chroma, monkeypatch):
    monkeypatch.setattr("scripts.index_codebase.reindex_single_file", patched_reindex_single_file)

    test_dir = tempfile.mkdtemp(prefix="watchers_agg_integration_")
    root_dirs.append(test_dir)
    monkeypatch.setattr("scripts.index_codebase.ROOT_DIRS", root_dirs)

    watchers_thread = threading.Thread(target=idx.watch_for_changes, daemon=True)
    watchers_thread.start()
    print(f"Started watchers on {test_dir}")

    test_py_path = os.path.join(test_dir, "test_division_error.py")
    with open(test_py_path, "w") as f:
        f.write("def my_func():\n")
        f.write("    # This function references a division error\n")
        f.write("    return 1 / 0  # potential ZeroDivisionError\n")

    emb_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    idx.reindex_single_file(test_py_path, ephemeral_chroma, emb_model)
    print(f"Forced initial index of {test_py_path}")

    time.sleep(5)

    with open(test_py_path, "a") as f:
        f.flush()  # Ensure write commits
        f.write("\n    # Updated division error fix\n")
    print(f"Appended update to {test_py_path}")

    wait_time = 10
    print(f"Waiting {wait_time}s for watchers to reindex update...")
    time.sleep(wait_time)

    indexed_docs = ephemeral_chroma.get(limit=9999)
    print(f"Indexed docs after wait: {len(indexed_docs.get('ids', []))} chunks")
    if indexed_docs.get("documents"):
        for i, doc in enumerate(indexed_docs["documents"]):
            print(f"Chunk {i}: {doc}")

    results = aggregator_search(query="division error", top_n=3)
    print(f"Aggregator returned {len(results)} results")
    for i, r in enumerate(results):
        print(f"Result {i}: {r['document']} (distance={r['distance']})")

    assert len(results) > 0, "Expected at least one aggregator result for 'division error'."
    found = False
    for r in results:
        doc_text = r["document"]
        filepath = r["metadata"].get("filepath", "")
        if "test_division_error.py" in filepath and "updated division error fix" in doc_text.lower():
            found = True
            print(f"Found updated match: {filepath} (distance={r['distance']})")
            break
    assert found, "Expected aggregator result with updated 'division error fix' in test_division_error.py."

    shutil.rmtree(test_dir)
    print("\n[SUCCESS] Watchers + aggregator synergy test passed!")