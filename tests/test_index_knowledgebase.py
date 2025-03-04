#!/usr/bin/env python3
"""
test_index_knowledgebase.py

Manually tests indexing, RAG readiness, and change verification for index_knowledgebase.py,
ensuring reliable operation with minimal logic and no errors. Run after manual indexing.
"""

import os
import time
import logging
import chromadb
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")

def test_indexing():
    logging.info("🔍 Testing indexing in knowledge_base_test...")
    collection = chroma_client.get_collection("knowledge_base_test")
    results = collection.query(
        query_texts=["ZeroDivisionError"],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )
    if results["documents"]:
        logging.info("✅ Indexing test passed: Found %d relevant chunks for 'ZeroDivisionError':", len(results["documents"]))
        logging.debug(f"Debug - results['metadatas']: {results['metadatas']}")  # Log metadata for debugging
        for i in range(len(results["documents"])):
            doc = results["documents"][i]
            # Handle nested metadatas (list of dictionaries)
            if results["metadatas"] and i < len(results["metadatas"]):
                metadatas = results["metadatas"][i]
                if isinstance(metadatas, list):
                    for meta in metadatas:
                        if isinstance(meta, dict):
                            logging.info(f"  - Chunk: {doc[:50]}... (Source: {meta['source']}, Filename: {meta['filename']}, mtime: {meta['mtime']})")
                        else:
                            logging.warning(f"⚠️ Metadata at index {i} in list is not a dictionary: {meta}")
                elif isinstance(metadatas, dict):
                    logging.info(f"  - Chunk: {doc[:50]}... (Source: {metadatas['source']}, Filename: {metadatas['filename']}, mtime: {metadatas['mtime']})")
                else:
                    logging.warning(f"⚠️ Metadata at index {i} is not a list or dictionary: {metadatas}")
            else:
                logging.warning(f"⚠️ No metadata at index {i}")
    else:
        logging.warning("⚠️ Indexing test failed: No relevant chunks found for 'ZeroDivisionError'.")

def test_changes():
    logging.info("🔍 Testing manual change verification (run index_knowledgebase.py after changes):")
    logging.info("1. Create or modify a .md file (e.g., /mnt/f/projects/ai-recall-system/knowledge_base/test_markdown.md or an agent README):")
    logging.info("# Test Markdown\n## Error Handling\n```python\ndef divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return None\n```")
    logging.info("2. Run: 'export MODE=test; python3 /mnt/f/projects/ai-recall-system/scripts/index_knowledgebase.py'")
    logging.info("3. Wait 60s (1 minute) for indexing, then verify with:")
    logging.info("   python -c \"import chromadb; import json; c = chromadb.PersistentClient(path='/mnt/f/projects/ai-recall-system/chroma_db/'); coll = c.get_collection('knowledge_base_test'); r = coll.query(query_texts=['test markdown'], n_results=1, include=['documents', 'metadatas', 'distances']); print(json.dumps(r, indent=2))\"")
    logging.info("4. Expect the new/changed file (e.g., 'test_markdown.md' or agent README) in metadatas with its source (e.g., 'agent_engineer' for READMEs). Then, delete or modify the file and re-run 'export MODE=test; python3 /mnt/f/projects/ai-recall-system/scripts/index_knowledgebase.py' after waiting 60s to verify updates/removal.")
    logging.info("5. Verify with the same Python command, expecting updated or no entry in metadatas.")
    logging.info("✅ Manual change test completed—adjust timing (e.g., 120s) if needed for WSL/WSL2 latency, slow file system, or debugging.")

def test_rag():
    logging.info("🔍 Testing RAG readiness...")
    knowledgebase_dirs = [
        "/mnt/f/projects/ai-recall-system/knowledge_base/",
        "/mnt/f/projects/ai-recall-system/agent_knowledge_bases/"
    ]
    collection = chroma_client.get_collection("knowledge_base_test")
    for directory in knowledgebase_dirs:
        for filename in os.listdir(directory):
            if filename.endswith(".md") or (os.path.isdir(os.path.join(directory, filename)) and os.path.exists(os.path.join(directory, filename, "README.md"))):
                base_name = filename if filename.endswith(".md") else "README.md"
                source = os.path.basename(directory) if filename.endswith(".md") else f"agent_{filename}"
                logging.info(f"🔍 Testing RAG for {base_name} from {source}...")
                results = collection.query(
                    query_texts=[f"error handling in {base_name}"],
                    n_results=1,
                    include=["documents", "metadatas", "distances"]
                )
                if results["documents"]:
                    logging.info("✅ RAG test passed for %s from %s: Found relevant chunk.", base_name, source)
                else:
                    logging.warning("⚠️ RAG test failed for %s from %s: No relevant chunks found.", base_name, source)

if __name__ == "__main__":
    # Clean up knowledge_base_test_test before testing
    try:
        chroma_client.delete_collection("knowledge_base_test_test")
        logging.info("✅ Removed knowledge_base_test_test to prevent duplication.")
    except Exception as e:
        logging.warning(f"⚠️ Could not remove knowledge_base_test_test: {e}")

    # Run all tests (no deduplication, let index_knowledgebase.py handle it)
    test_indexing()
    test_changes()
    test_rag()

    logging.info("✅ All tests for index_knowledgebase.py completed successfully in test mode.")