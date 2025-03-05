#!/usr/bin/env python3
"""
index_knowledgebase.py

Indexes markdown files from /knowledge_base and /agent_knowledge_bases into the knowledge_base ChromaDB collection,
deduplicating by mtime and hash, using a "newest version only" system. Run manually when markdowns change.
"""

import os
import re
import time
import logging
import hashlib
from pathlib import Path
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import chromadb

# Configure logging to file
LOG_FILE = "/mnt/f/projects/ai-recall-system/logs/script_logs/index_knowledgebase.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize ChromaDB and embeddings
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def chunk_markdown(text, chunk_size=500):
    """
    Chunks markdown text into segments of approximately chunk_size characters,
    preserving section boundaries where possible.
    """
    sections = re.split(r"\n#{1,6}\s+", text)  # Split by markdown headers
    chunks = []
    current_chunk = ""
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().split("\n")
        for line in lines:
            if len(current_chunk) + len(line) + 1 > chunk_size:  # +1 for newline
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                current_chunk += "\n" + line if current_chunk else line
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def get_file_hash(filepath):
    """
    Generates a SHA-256 hash of a file's content for deduplication.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def index_markdown_file(markdown_path, collection_name="knowledge_base"):
    """
    Indexes a single markdown file into the specified ChromaDB collection,
    deduplicating by mtime and hash, using a "newest version only" system.
    Adds agent identifier for READMEs in /agent_knowledge_bases.
    """
    try:
        # Determine test mode from environment or default to False
        test_mode = "test" in os.environ.get("MODE", "").lower()
        collection_name = f"{collection_name}_test" if test_mode else collection_name

        # Get file metadata for deduplication
        mtime = Path(markdown_path).stat().st_mtime
        file_hash = get_file_hash(markdown_path)

        # Read the markdown file
        with open(markdown_path, "r", encoding="utf-8") as f:
            markdown_text = f.read()

        # Generate a unique ID (no versioning, just filename-based with agent identifier if applicable)
        base_name = os.path.basename(markdown_path)
        if "agent_knowledge_bases" in markdown_path:
            # Extract agent name from path (e.g., engineer_knowledge from .../engineer_knowledge/README.md)
            agent_name = Path(markdown_path).parent.name
            doc_id = f"{agent_name}_{base_name}"
        else:
            doc_id = base_name

        # Chunk the markdown
        chunks = chunk_markdown(markdown_text)
        collection = chroma_client.get_or_create_collection(name=collection_name)

        # Check for existing versions by filename, mtime, and hash
        existing_docs = collection.get(
            where={"filename": base_name}
        )["metadatas"] if collection.count() > 0 else []
        should_index = True
        for meta in existing_docs:
            if meta.get("mtime", 0) == mtime and meta.get("hash", "") == file_hash:
                logger.info(f"✅ Skipped indexing {base_name}: No changes detected (mtime: {mtime}, hash: {file_hash}).")
                should_index = False
                break

        if should_index:
            # Clean up any old versions of this file (keep only newest)
            collection.delete(
                where={"filename": base_name}
            )
            logger.info(f"🗑️ Removed old version of {base_name} from {collection_name}.")

            # Store each chunk with metadata (no version, just mtime, hash, and agent if applicable)
            for i, chunk in enumerate(chunks):
                metadata = {
                    "filename": base_name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source": os.path.dirname(markdown_path).split("/")[-1] if "agent_knowledge_bases" not in markdown_path else f"agent_{agent_name}",
                    "mtime": mtime,
                    "hash": file_hash
                }
                collection.upsert(
                    ids=[f"{doc_id}_{i}"],
                    documents=[chunk],
                    metadatas=[metadata]
                )
            logger.info(f"✅ Indexed {base_name} into {collection_name} with {len(chunks)} chunks.")
        return True
    except Exception as e:
        logger.error(f"❌ Error indexing {os.path.basename(markdown_path)}: {e}")
        return False

if __name__ == "__main__":
    # Define directories to index
    knowledgebase_dirs = [
        "/mnt/f/projects/ai-recall-system/knowledge_base/",
        "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/"
    ]

    # Clean up knowledge_base_test_test if it exists before starting
    try:
        chroma_client.delete_collection("knowledge_base_test_test")
        logger.info("✅ Removed knowledge_base_test_test to prevent duplication.")
    except Exception as e:
        logger.warning(f"⚠️ Could not remove knowledge_base_test_test: {e}")

    # Index existing markdown files, checking for duplicates
    total_indexed = 0
    for directory in knowledgebase_dirs:
        if "agent_knowledge_bases" in directory:
            # Index README.md files from each agent subfolder
            for agent_dir in os.listdir(directory):
                agent_path = os.path.join(directory, agent_dir)
                if os.path.isdir(agent_path):
                    readme_path = os.path.join(agent_path, "README.md")
                    if os.path.exists(readme_path):
                        if index_markdown_file(readme_path):
                            total_indexed += 1
        else:
            # Index all .md files in knowledge_base
            for filename in os.listdir(directory):
                if filename.endswith(".md"):
                    markdown_path = os.path.join(directory, filename)
                    if index_markdown_file(markdown_path):
                        total_indexed += 1

    logger.info(f"✅ index_knowledgebase.py completed indexing successfully in test mode with {total_indexed} files.")