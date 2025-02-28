import os
import pytest
import json
from unittest.mock import patch
import chromadb

import scripts.retrieve_codebase as rcode

@pytest.fixture
def codebase_test_coll():
    # ephemeral test coll
    client = chromadb.PersistentClient(path=rcode.CHROMA_DB_PATH)
    coll = client.get_or_create_collection(name="project_codebase_test")
    yield coll
    # cleanup
    results = coll.get(limit=9999)
    if "ids" in results and results["ids"]:
        coll.delete(ids=results["ids"])

def test_naive_substring_search(codebase_test_coll):
    """
    We'll add a doc chunk with known substring, then do naive_substring_search.
    """
    doc_text = "Here is a magic_substring for naive test."
    codebase_test_coll.add(
        documents=[doc_text],
        embeddings=[[0]*384],  # dummy embedding, length 384 to match the MiniLM dimension
        metadatas=[{"rel_path": "fake.md", "chunk_index": 0}],
        ids=["fake_doc_001"]
    )

    # We'll build the docs dict
    all_docs = codebase_test_coll.get(limit=10)
    docs_dict = {
        "documents": all_docs["documents"],
        "metadatas": all_docs["metadatas"],
        "ids": all_docs["ids"]
    }

    results = rcode.naive_substring_search(docs_dict, query="magic_substring")
    assert len(results) == 1, "Expected 1 match for 'magic_substring'"
    doc_text2, meta, doc_id = results[0]
    assert doc_id == "fake_doc_001"
    assert meta["rel_path"] == "fake.md"
    assert "magic_substring" in doc_text2

def test_embedding_search(codebase_test_coll):
    """
    We'll add a doc chunk with known text, store a real embedding, then do an embedding search
    for a semantically-related phrase. We'll expect 1 match.
    """
    # We'll embed the doc
    from langchain_community.embeddings import HuggingFaceEmbeddings
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    doc_text = "We handle a ZeroDivisionError in this code chunk."
    doc_embedding = emb.embed_documents([doc_text])[0]

    codebase_test_coll.add(
        documents=[doc_text],
        embeddings=[doc_embedding],
        metadatas=[{"filepath": "fake.py", "chunk_index": 0}],
        ids=["fake_doc_002"]
    )

    # Now do an embedding_search with a related phrase
    results = rcode.embedding_search(codebase_test_coll, query="division by zero", n_results=2)
    assert len(results) == 1, "Expected a single semantic match for 'division by zero'"
    matched_text, matched_meta, matched_id = results[0]
    assert matched_id == "fake_doc_002"
    assert "ZeroDivisionError" in matched_text
    assert matched_meta["filepath"] == "fake.py"
