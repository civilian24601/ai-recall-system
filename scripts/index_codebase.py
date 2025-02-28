#!/usr/bin/env python3
"""
index_codebase.py 

 - Uses Python AST for .py files to chunk each function/class with docstrings.
 - For large functions/classes, we further chunk them line-based.
 - For non-Python files (JS, TS, MD, JSON, etc.), we do line-based chunking with line-range metadata.
   - Special handling for .md: smaller chunk size (100 lines) + 20-line overlap.
   - Markdowns in 'knowledge_base' folder get a 'guideline': True metadata flag.
 - We store 'start_line','end_line','function_name','class_name','node_type' in metadata, ensuring no None values.
 - Watchers with debouncing for partial saves, rename & delete handling.
 - Root directory covers the entire project ("/mnt/f/projects/ai-recall-system").
 
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
import ast

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

CHUNK_SIZE_DEFAULT = 300    # lines, for most files
CHUNK_SIZE_MD = 100         # smaller chunk size for markdown files
CHUNK_OVERLAP_PY = 50       # only used when chunking large Python function bodies
CHUNK_OVERLAP_MD = 20       # overlap for markdown files
ALLOWED_EXTENSIONS = {".py", ".md", ".json", ".txt", ".yml", ".toml", ".js", ".ts"}
SKIP_DIRS = {
    "chroma_db", ".git", "__pycache__", ".idea", "venv", ".pytest_cache", 
    "node_modules", ".next", "dist"
}
SKIP_FILES = {"codebase_inventory.md", "compiled_knowledge.md"}

ROOT_DIRS = ["/mnt/f/projects/ai-recall-system"]  # Index entire project
DEBOUNCE_SECONDS = 2.0

# If AST parse fails, do we fallback to line-based chunking for .py? We'll say yes:
LINE_BASED_CHUNKING_PY_FALLBACK = True

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
# PYTHON AST CHUNKING
##############################################################################

class PyFunctionChunk:
    """
    Represents a function/method/class node with line info from AST.
    """
    def __init__(self, name, start_line, end_line, node_type="function", parent_class=None):
        self.name = name
        self.start_line = start_line
        self.end_line = end_line
        self.node_type = node_type  # "function", "method", "class", etc.
        self.parent_class = parent_class  # if it's a method in a class

def parse_python_ast(filepath):
    """Parse the Python file with ast, return a list of PyFunctionChunk objects."""
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    try:
        tree = ast.parse(code)
    except Exception as e:
        print(f"⚠ AST parse error in {filepath}: {e}")
        return []

    results = []
    class ASTVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            parent_cls = getattr(node, "_parent_class", None)
            name = node.name
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            node_type = "function" if not parent_cls else "method"
            results.append(PyFunctionChunk(name, start_line, end_line, node_type, parent_cls))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            parent_cls = getattr(node, "_parent_class", None)
            name = node.name
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            node_type = "async_function" if not parent_cls else "async_method"
            results.append(PyFunctionChunk(name, start_line, end_line, node_type, parent_cls))
            self.generic_visit(node)

        def visit_ClassDef(self, node):
            class_name = node.name
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            results.append(PyFunctionChunk(class_name, start_line, end_line, "class"))
            # mark child methods
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    child._parent_class = class_name
            self.generic_visit(node)

    ASTVisitor().visit(tree)
    return results

def build_python_chunks(lines, func_chunk):
    """
    For each PyFunctionChunk, we slice out lines from start_line-1..end_line
    and if bigger than CHUNK_SIZE_DEFAULT, chunk it. Return a list of dicts with
    "text", "start_line", "end_line", "function_name", "class_name", "node_type".
    """
    start_idx = func_chunk.start_line - 1
    end_idx = func_chunk.end_line
    snippet_lines = lines[start_idx:end_idx]

    big_chunks = chunk_lines_with_range(snippet_lines, start_idx, CHUNK_SIZE_DEFAULT, overlap=CHUNK_OVERLAP_PY)
    output = []
    for (chunk_text, real_start, real_end) in big_chunks:
        output.append({
            "text": chunk_text,
            "start_line": real_start + 1,  # convert to 1-based
            "end_line": real_end + 1,
            "function_name": func_chunk.name if func_chunk.node_type in ("function","method","async_function","async_method") else "",
            "class_name": func_chunk.parent_class if func_chunk.parent_class else (func_chunk.name if func_chunk.node_type=="class" else ""),
            "node_type": func_chunk.node_type
        })
    return output

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
        print(f"⚠ Error reading {filepath}: {e}")
        return 0

    if not text.strip():
        return 0

    # Remove old doc_ids for this file
    existing = collection.get(limit=9999)
    if existing and "ids" in existing and existing["ids"]:
        matched_ids = []
        for doc_id in existing["ids"]:
            if doc_id.startswith(f"{filepath}::chunk_"):
                matched_ids.append(doc_id)
        if matched_ids:
            collection.delete(ids=matched_ids)
            print(f"   🔸 Removed {len(matched_ids)} old chunk(s) for updated file: {filepath}")

    lines = text.splitlines()
    new_chunks_for_file = 0

    if ext == ".py":
        func_chunks = parse_python_ast(filepath)
        py_chunks = []
        if not func_chunks:
            # Fallback => line-based chunk
            line_blocks = chunk_lines_with_range(lines, 0, chunk_size=CHUNK_SIZE_DEFAULT, overlap=0)
            for chunk_text, st_line, end_line in line_blocks:
                py_chunks.append({
                    "text": chunk_text,
                    "start_line": st_line+1,
                    "end_line": end_line+1,
                    "function_name": "",
                    "class_name": "",
                    "node_type": "misc"
                })
        else:
            # Chunk each function/class
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

            # Replace None with "" just in case
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
                "start_line": start_line,  # Fixed: Use start_line from cdict
                "end_line": end_line,      # Fixed: Use end_line from cdict
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

    else:
        # Non-Python => line-based chunk with line-range
        # Use smaller chunk size and overlap for .md files
        chunk_size = CHUNK_SIZE_MD if ext == ".md" else CHUNK_SIZE_DEFAULT
        overlap = CHUNK_OVERLAP_MD if ext == ".md" else 0
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
                "function_name": "",
                "class_name": "",
                "node_type": "lines",
                "guideline": True if (ext == ".md" and "knowledge_base" in filepath) else False,
                "naive_only": True if ext != ".md" else False  # Naive-only for non-markdown non-Python
            }

            collection.add(
                documents=[chunk_text],
                embeddings=[embedding],
                metadatas=[meta],
                ids=[doc_id]
            )
            new_chunks_for_file += 1

    if new_chunks_for_file > 0:
        print(f"   ⮑ Re-indexed {new_chunks_for_file} chunk(s) from {filepath}")

    return new_chunks_for_file

##############################################################################
# One-shot indexing
##############################################################################

def index_codebase():
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' ...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    total_files = 0
    total_new_chunks = 0

    for root_dir in ROOT_DIRS:
        if not os.path.exists(root_dir):
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
            print(f"\n🔄 File renamed from {event.src_path} -> {event.dest_path}")
            self.remove_file_chunks(event.src_path)
            ext = os.path.splitext(event.dest_path)[1].lower()
            if ext in ALLOWED_EXTENSIONS:
                self._handle_change(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory:
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
                print(f"   🔸 Removed {len(matched_ids)} chunk(s) for deleted/renamed file: {filepath}")

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

        print(f"\n🔄 Debounced re-index for file: {filepath}")
        reindex_single_file(filepath, self.collection, self.embed_model)

def watch_for_changes():
    print(f"🔗 Connecting to Chroma at '{CHROMA_DB_PATH}' for watchers...")
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    event_handler = CodebaseEventHandler(collection, embed_model)
    observer = watchdog.observers.Observer()

    for root_dir in ROOT_DIRS:
        if os.path.exists(root_dir):
            observer.schedule(event_handler, path=root_dir, recursive=True)
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
    parser = argparse.ArgumentParser(description="Index codebase + watchers + AST-based Python chunking.")
    parser.add_argument("--watch", action="store_true", help="Watch for file changes in real time.")
    args = parser.parse_args()

    if args.watch:
        watch_for_changes()
    else:
        index_codebase()