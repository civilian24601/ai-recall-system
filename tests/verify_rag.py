#!/usr/bin/env python3
"""
verify_rag.py

Verifies RAG readiness by querying 'ZeroDivisionError', 'test markdown', and 'edge case test' in knowledge_base_test,
ensuring full output and validating expected chunks from ai_coding_guidelines.md, test_markdown.md, and edge_case_test.md.
"""

import chromadb
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
collection = chroma_client.get_collection("knowledge_base_test")

# Query for ZeroDivisionError
results_zero = collection.query(
    query_texts=["ZeroDivisionError"],
    n_results=3,
    include=["documents", "metadatas", "distances"]
)

# Query for test_markdown
results_test = collection.query(
    query_texts=["test markdown"],
    n_results=1,
    include=["documents", "metadatas", "distances"]
)

# Query for edge_case_test
results_edge = collection.query(
    query_texts=["edge case test"],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

# Print full results for ZeroDivisionError
logging.info("Full Query Results for 'ZeroDivisionError':")
logging.info(json.dumps(results_zero, indent=2))

# Print full results for 'test markdown'
logging.info("Full Query Results for 'test markdown':")
logging.info(json.dumps(results_test, indent=2))

# Print full results for 'edge case test'
logging.info("Full Query Results for 'edge case test':")
logging.info(json.dumps(results_edge, indent=2))

# Verify specific chunk from ai_coding_guidelines.md
expected_chunk_zero = "def divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:"
found_match_zero = False
for doc, meta in zip(results_zero["documents"][0], results_zero["metadatas"][0]):
    if isinstance(meta, dict) and expected_chunk_zero in doc and meta["filename"] == "ai_coding_guidelines.md":
        found_match_zero = True
        logging.info(f"✅ Found expected chunk in {meta['filename']} with source: {meta['source']}, mtime: {meta['mtime']}")
if not found_match_zero:
    logging.warning("⚠️ Did not find expected chunk from ai_coding_guidelines.md in ZeroDivisionError results.")

# Verify specific chunk from test_markdown.md (flexible check for content)
found_match_test = False
for doc, meta in zip(results_test["documents"][0], results_test["metadatas"][0]):
    if isinstance(meta, dict) and meta["filename"] == "test_markdown.md":
        if "test markdown" in doc or "testing at 230pm" in doc:
            found_match_test = True
            logging.info(f"✅ Found expected content in {meta['filename']} with source: {meta['source']}, mtime: {meta['mtime']}")
if not found_match_test:
    logging.warning("⚠️ Did not find expected content from test_markdown.md in test markdown results.")

# Verify specific chunk from edge_case_test.md (specific check for content)
found_match_edge = False
for doc, meta in zip(results_edge["documents"][0], results_edge["metadatas"][0]):
    if isinstance(meta, dict) and meta["filename"] == "edge_case_test.md":
        if "# Edge Case Test Document" in doc or "Very Long Text for Chunking" in doc:
            found_match_edge = True
            logging.info(f"✅ Found expected content in {meta['filename']} with source: {meta['source']}, mtime: {meta['mtime']}")
if not found_match_edge:
    logging.warning("⚠️ Did not find expected content from edge_case_test.md in edge case test results.")