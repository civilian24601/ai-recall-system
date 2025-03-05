#!/usr/bin/env python3
"""
index_codebase.py 

 - Uses line-based chunking for code files (.py, .js, .tsx).
 - For large chunks, we split line-based with overlap.
 - No markdown or JSON files—those are handled by knowledge_base_test and debugging_logs collections.
 - We store 'start_line','end_line','function_name','class_name','node_type' in metadata, ensuring no None values.
 - Watchers with debouncing for partial saves, rename & delete handling.
 - Root directory covers /code_base, /scripts, /tests, /frontend (no node_modules, dist, etc.).
 
Usage:
    python index_codebase.py
        (one-shot indexing)
    python index_codebase.py --watch
        (start watchers in real-time)
"""

import os
import sys
import time
import hashlib
import threading
import logging

import chromadb
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

import watchdog.events
import watchdog.observers
from watchdog.events import FileSystemEventHandler

##############################################################################
# CONFIG
##############################################################################

CHROMA_DB_PATH = "/mnt/f/projects/ai-recall-system/chroma_db"
COLLECTION_NAME = "project_codebase"
LOG_FILE = "/mnt/f/projects/ai-recall-system/logs/script_logs/index_codebase.log"

CHUNK_SIZE_DEFAULT = 300    # lines, for all code files
CHUNK_OVERLAP = 50         # overlap for all code files
ALLOWED_EXTENSIONS = {".py", ".js", ".tsx"}  # Only code files, no markdown or JSON
SKIP_DIRS = {
    "chroma_db", ".git", "__pycache__", ".idea", "venv", ".pytest_cache", 
    "node_modules", ".next", "dist", "archive", "knowledge_base", "agent_knowledge_bases", "logs"
}
SKIP_FILES = {"codebase_inventory.md", "compiled_knowledge.md"}  # Keep these skipped

ROOT_DIRS = ["/mnt/f/projects/ai-recall-system/code_base", 
             "/mnt/f/projects/ai-recall-system/scripts", 
             "/mnt/f/projects/ai-recall-system/tests", 
             "/mnt/f/projects/ai-recall-system/frontend"]  # Focus on code directories
DEBOUNCE_SECONDS = 2.0

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

##############################################################################
# UTILS
##############################################################################

def compute_md5_hash(text: str) -> str:
    normalized = text.strip().replace("\r\n", "\n")
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()

def chunk_lines_with_range(lines, start_idx, chunk_size=300, overlap=0):
    """
    Takes a list of lines (strings) and returns a list of
    (chunk_text, start_line, end_line).
    If overlap > 0, we do partial overlap.
    """
    i = 0
    results = []
    n = len(lines)
    while i < n:
        end = min(i + chunk_size, n)
        chunk_slice = lines[i:end]
        chunk_text = "\n".join(chunk_slice)
        real_start = start_idx + i
        real_end = start_idx + end - 1

        results.append((chunk_text, real_start, real_end))
        if overlap == 0:
            i = end
        else:
            i += (chunk_size - overlap)
    return results

##############################################################################
# reindex_single_file
##############################################################################

def reindex_single_file(filepath, collection, embed_model):
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return 0
    if not os.path.exists(filepath) or os.path.isdir(filepath):
        return 0
    if os.path.basename(filepath) in SKIP_FILES:
        return 0

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        print(f"⚠ Error reading {filepath}: {e}")
        return 0

    if not text.strip():
        return 0

    # Remove old doc_ids for this file
    existing_results = collection.get(limit=9999)
    if existing_results and "ids" in existing_results and existing_results["ids"]:
        matched_ids = []
        for doc_id in existing_results["ids"]:
            if doc_id.startswith(f"{filepath}::chunk_"):
                matched_ids.append(doc_id)
        if matched_ids:
            collection.delete(ids=matched_ids)
            logger.info(f"Removed {len(matched_ids)} old chunk(s) for updated file: {filepath}")
            print(f"   🔸 Removed {len(matched_ids)} old chunk(s) for updated file: {filepath}")

    lines = text.splitlines()
    new_chunks_for_file = 0

    # Use line-based chunking for all code files
    chunk_size = CHUNK_SIZE_DEFAULT
    overlap = CHUNK_OVERLAP
    line_blocks = chunk_lines_with_range(lines, 0, chunk_size=chunk_size, overlap=overlap)
    for idx, (chunk_text, st_line, end_line) in enumerate(line_blocks):
        if not chunk_text.strip():
            continue
        chunk_hash = compute_md5_hash(chunk_text)
        doc_id = f"{filepath}::chunk_{idx}::hash_{chunk_hash}"

        embedding = embed_model.embed_documents([chunk_text])[0]

        meta = {
            "filepath": filepath,
            "rel_path": filepath,
            "chunk_index": idx,
            "hash": chunk_hash,
            "mod_time": os.path.getmtime(filepath),
            "start_line": int(st_line),
            "end_line": int(end_line),
            "function_name": "",  # Empty for now, as we’re not using AST
            "class_name": "",     # Empty for now, as we’re not using AST
            "node_type": "lines"  # Generic for all code files
        }

        collection.add(
            documents=[chunk_text],
            embeddings=[embedding],
            metadatas=[meta],
            ids=[doc_id]
        )
        new_chunks_for_file += 1

    if new_chunks_for_file > 0:
        logger.info(f"Re-indexed {new_chunks_for_file} chunk(s) from {filepath}")
        print(f"   ⮑ Re-indexed {new_chunks_for_file} chunk(s) from {filepath}")

    return new_chunks_for_file

##############################################################################
# One-shot indexing
##############################################################################

def index_codebase():
    logger.info(f"Connecting to Chroma at '{CHROMA_DB_PATH}'")
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' ...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total_files = 0
    total_new_chunks = 0

    for root_dir in ROOT_DIRS:
        if not os.path.exists(root_dir):
            logger.warning(f"Root dir not found: {root_dir}. Skipping.")
            print(f"⚠ Root dir not found: {root_dir}. Skipping.")
            continue

        for current_root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for filename in files:
                filepath = os.path.join(current_root, filename)
                added = reindex_single_file(filepath, collection, embed_model)
                if added > 0:
                    total_files += 1
                    total_new_chunks += added

    logger.info(f"Done indexing. Processed {total_files} files total. Added {total_new_chunks} new chunks.")
    print(f"\n✅ Done indexing. Processed {total_files} files total. Added {total_new_chunks} new chunks.")

##############################################################################
# Watchers
##############################################################################

class CodebaseEventHandler(FileSystemEventHandler):
    def __init__(self, collection, embed_model):
        super().__init__()
        self.collection = collection
        self.embed_model = embed_model
        self._pending_changes = {}
        self._lock = threading.Lock()

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._handle_change(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            logger.info(f"File renamed from {event.src_path} -> {event.dest_path}")
            print(f"\n🔄 File renamed from {event.src_path} -> {event.dest_path}")
            self.remove_file_chunks(event.src_path)
            ext = os.path.splitext(event.dest_path)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                self._handle_change(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory:
            logger.info(f"File deleted: {event.src_path}, removing old chunks.")
            print(f"\n❌ File deleted: {event.src_path}, removing old chunks.")
            self.remove_file_chunks(event.src_path)

    def remove_file_chunks(self, filepath):
        existing_results = self.collection.get(limit=9999)
        if existing_results and "ids" in existing_results and existing_results["ids"]:
            matched_ids = []
            for doc_id in existing_results["ids"]:
                if doc_id.startswith(f"{filepath}::chunk_"):
                    matched_ids.append(doc_id)
            if matched_ids:
                self.collection.delete(ids=matched_ids)
                logger.info(f"Removed {len(matched_ids)} old chunk(s) for deleted/renamed file: {filepath}")
                print(f"   🔸 Removed {len(matched_ids)} old chunk(s) for deleted/renamed file: {filepath}")

    def _handle_change(self, filepath):
        with self._lock:
            self._pending_changes[filepath] = time.time()
        threading.Thread(target=self._debounce_and_index, args=(filepath,)).start()

    def _debounce_and_index(self, filepath):
        time.sleep(DEBOUNCE_SECONDS)
        with self._lock:
            last_t = self._pending_changes.get(filepath, None)
            if not last_t:
                return
            if (time.time() - last_t) >= DEBOUNCE_SECONDS:
                self._pending_changes.pop(filepath, None)
            else:
                return

        logger.info(f"Debounced re-index for file: {filepath}")
        print(f"\n🔄 Debounced re-index for file: {filepath}")
        reindex_single_file(filepath, self.collection, self.embed_model)

def watch_for_changes():
    logger.info(f"Connecting to Chroma at '{CHROMA_DB_PATH}' for watchers...")
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' for watchers...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    event_handler = CodebaseEventHandler(collection, embed_model)
    observer = watchdog.observers.Observer()

    for root_dir in ROOT_DIRS:
        if os.path.exists(root_dir):
            observer.schedule(event_handler, path=root_dir, recursive=True)
            logger.info(f"Watching {root_dir} for changes...")
            print(f"👀 Watching {root_dir} for changes...")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Index codebase + watchers + line-based chunking for code files only.")
    parser.add_argument("--watch", action="store_true", help="Watch for file changes in real time.")
    args = parser.parse_args()

    if args.watch:
        watch_for_changes()
    else:
        index_codebase()