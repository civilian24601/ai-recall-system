#!/usr/bin/env python3
"""
index_codebase.py

Indexes your entire project (or selected subdirs) into ChromaDB, chunking files
and storing them with stable doc_ids that incorporate a hash of the chunk.
- If a chunk is unchanged, it won't be duplicated.
- If a chunk changes, a new doc_id is created, preserving the old version.

This script can be safely run multiple times; only changed/new chunks get added.

NOTE: We explicitly set model_name="sentence-transformers/all-MiniLM-L6-v2"
(384-dimensional) so it matches your older logs/blueprints. That prevents
dimension mismatch in aggregator_search.
"""

import os
import sys
import hashlib
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
# If you get an import error, do: pip install -U langchain-community

###############################################################################
# 1) CONFIGURABLE CONSTANTS
###############################################################################

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"

CHUNK_SIZE = 300  # lines or words
CHUNK_OVERLAP = 50  # only used if line-based is False
ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".txt", ".yml", ".toml"}
SKIP_DIRS = {"chroma_db", ".git", "__pycache__", ".idea", "venv"}
SKIP_FILES = {"codebase_inventory.md", "compiled_knowledge.md"}

ROOT_DIRS = [
    "/mnt/f/projects/ai-recall-system/code_base",
    "/mnt/f/projects/ai-recall-system/knowledge_base",
    "/mnt/f/projects/ai-recall-system/scripts",
]

# If True, chunk by lines. If False, chunk by words (with overlap).
LINE_BASED_CHUNKING = False

###############################################################################
# 2) HELPER FUNCTIONS
###############################################################################

def compute_md5_hash(text: str) -> str:
    normalized = text.strip().replace("\r\n", "\n")
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

def chunk_by_lines(full_text: str, chunk_size: int = 300):
    lines = full_text.splitlines()
    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunk_slice = lines[i : i + chunk_size]
        chunk_str = "\n".join(chunk_slice)
        chunks.append(chunk_str)
    return chunks

def chunk_by_words(full_text: str, chunk_size=300, overlap=50):
    words = full_text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = words[start:end]
        chunk_str = " ".join(chunk)
        if chunk_str.strip():
            chunks.append(chunk_str)
        start += (chunk_size - overlap)
    return chunks

###############################################################################
# 3) MAIN INDEX FUNCTION
###############################################################################

def index_codebase():
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' ...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # Use 384-dim model so aggregator_search is consistent across logs + code
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total_new_chunks = 0
    total_files = 0

    for root_dir in ROOT_DIRS:
        if not os.path.exists(root_dir):
            print(f"⚠ Root dir not found: {root_dir}. Skipping.")
            continue

        for current_root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    continue
                if filename in SKIP_FILES:
                    continue

                filepath = os.path.join(current_root, filename)
                rel_path = os.path.relpath(filepath, start=root_dir)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception as e:
                    print(f"⚠ Error reading {filepath}: {e}")
                    continue

                if not text.strip():
                    continue
                total_files += 1

                # chunk
                if LINE_BASED_CHUNKING:
                    chunks = chunk_by_lines(text, CHUNK_SIZE)
                else:
                    chunks = chunk_by_words(text, CHUNK_SIZE, CHUNK_OVERLAP)

                new_chunks_for_file = 0
                for idx, chunk_str in enumerate(chunks):
                    if not chunk_str.strip():
                        continue
                    chunk_hash = compute_md5_hash(chunk_str)
                    doc_id = f"{filepath}::chunk_{idx}::hash_{chunk_hash}"

                    existing = collection.get(ids=[doc_id])
                    if existing and existing["ids"]:
                        continue

                    embedding = embed_model.embed_documents([chunk_str])[0]
                    meta = {
                        "filepath": filepath,
                        "rel_path": rel_path,
                        "chunk_index": idx,
                        "hash": chunk_hash,
                        "mod_time": os.path.getmtime(filepath),
                    }
                    collection.add(
                        documents=[chunk_str],
                        embeddings=[embedding],
                        metadatas=[meta],
                        ids=[doc_id]
                    )
                    new_chunks_for_file += 1

                if new_chunks_for_file > 0:
                    print(f"   ⮑ Indexed {new_chunks_for_file} new chunk(s) from {filepath}")
                    total_new_chunks += new_chunks_for_file

    print(f"\n✅ Done indexing. Processed {total_files} files total. Added {total_new_chunks} new chunks.")

###############################################################################
# 4) ENTRY POINT
###############################################################################

if __name__ == "__main__":
    index_codebase()
