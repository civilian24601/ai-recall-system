import pytest
import os
import chromadb
import json
from unittest.mock import patch

import scripts.aggregator_search as aggscript

@pytest.fixture
def ephemeral_collections():
    """
    Creates two or three ephemeral test collections in Chroma.
    We'll add some doc chunks referencing e.g. 'magic_substring' or 'division error'.
    Then we unify them.
    """
    client = chromadb.PersistentClient(path=aggscript.CHROMA_PATH)
    
    # Let's define 2 ephemeral collections for the test
    c1 = client.get_or_create_collection("test_agg_coll1")
    c2 = client.get_or_create_collection("test_agg_coll2")

    # Cleanup any existing docs
    for c in [c1, c2]:
        results = c.get(limit=9999)
        if results and "ids" in results and results["ids"]:
            c.delete(ids=results["ids"])

    yield (c1, c2)

    # teardown
    for c in [c1, c2]:
        results = c.get(limit=9999)
        if results and "ids" in results and results["ids"]:
            c.delete(ids=results["ids"])


def test_aggregator_search_embedding(ephemeral_collections):
    """
    We do an ephemeral embedding aggregator test.
    We'll add a chunk referencing 'division error' to c1, 
    a chunk referencing 'magic_substring' to c2, 
    and then aggregator should unify them sorted by distance.
    """
    c1, c2 = ephemeral_collections

    # We'll do actual embeddings for the doc referencing 'division error'
    from langchain_huggingface.embeddings import HuggingFaceEmbeddings  # Not langchain_community!
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    doc_text_1 = "This chunk references a division error in the code."
    doc_emb_1 = emb.embed_documents([doc_text_1])[0]
    c1.add(
        documents=[doc_text_1],
        embeddings=[doc_emb_1],
        metadatas=[{"file": "div_err.py"}],
        ids=["doc_div_001"]
    )

    doc_text_2 = "Magic_substring is found here for aggregator test."
    doc_emb_2 = emb.embed_documents([doc_text_2])[0]
    c2.add(
        documents=[doc_text_2],
        embeddings=[doc_emb_2],
        metadatas=[{"file": "magic.txt"}],
        ids=["doc_magic_002"]
    )

    # Now aggregator
    # We'll monkeypatch the aggregator's COLLECTIONS_TO_QUERY to only use these ephemeral coll names.
    with patch.object(aggscript, "COLLECTIONS_TO_QUERY", new=["test_agg_coll1", "test_agg_coll2"]):
        results = aggscript.aggregator_search("division error", top_n=3)
        # We expect doc_div_001 to appear first or near, doc_magic_002 might appear but likely with higher distance
        assert len(results) >= 2, "We expect at least 2 results (one from each collection)."
        # doc_div_001 should have smaller distance if searching 'division error'
        # doc_magic_002 might have a bigger distance
        # We can confirm the first result is doc_div_001
        assert results[0]["metadata"].get("file") == "div_err.py"

def test_aggregator_search_naive(ephemeral_collections):
    """
    We'll do naive substring aggregator. We'll store docs w/ no embeddings.
    aggregator_search in naive or both mode => unify substring hits.
    """
    c1, c2 = ephemeral_collections

    doc_text_1 = "This chunk references a division error in the code."
    c1.add(
        documents=[doc_text_1],
        embeddings=[[0]*384], # dummy embedding
        metadatas=[{"file": "div_err.py"}],
        ids=["doc_div_001"]
    )

    doc_text_2 = "Magic_substring is found here for aggregator test."
    c2.add(
        documents=[doc_text_2],
        embeddings=[[0]*384],
        metadatas=[{"file": "magic.txt"}],
        ids=["doc_magic_002"]
    )

    # Now aggregator in naive mode:
    with patch.object(aggscript, "COLLECTIONS_TO_QUERY", new=["test_agg_coll1", "test_agg_coll2"]):
        results = aggscript.aggregator_search("division error", top_n=5, mode="naive")
        # This time, we expect doc_div_001 to appear because substring match "division error"
        # doc_magic_002 won't appear for that query
        assert len(results) == 1, "Expected only 1 naive substring match"
        assert results[0]["metadata"].get("file") == "div_err.py"

def test_aggregator_search_both(ephemeral_collections):
    """
    We'll store an actual embedding doc referencing 'division error'
    and a second doc referencing 'division error' but substring only
    Then aggregator in mode=both => unify embedding + naive. 
    The embedding doc should appear first (distance < 9).
    """
    c1, c2 = ephemeral_collections

    # doc w/ actual embed
    from langchain_huggingface.embeddings import HuggingFaceEmbeddings  # Not langchain_community!
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    doc_text_1 = "We definitely mention 'division error' here for real embedding approach."
    doc_emb_1 = emb.embed_documents([doc_text_1])[0]
    c1.add(
        documents=[doc_text_1],
        embeddings=[doc_emb_1],
        metadatas=[{"file": "embedded_div.py"}],
        ids=["doc_embed_div_001"]
    )

    # doc w/ substring only
    doc_text_2 = "some random text that also says DIVIZION error"
    c2.add(
        documents=[doc_text_2],
        embeddings=[[0]*384],
        metadatas=[{"file": "naive_div.txt", "naive_only": True}],
        ids=["doc_naive_div_002"]
    )

    with patch.object(aggscript, "COLLECTIONS_TO_QUERY", new=["test_agg_coll1", "test_agg_coll2"]):
        results = aggscript.aggregator_search("division error", top_n=5, mode="both")
        # We expect 2 matches total
        assert len(results) == 2
        # The first match => doc_embed_div_001 b/c distance ~ something < 9
        # The second => doc_naive_div_002 w/ distance = 9.0 + rank
        assert results[0]["metadata"].get("file") == "embedded_div.py"
        assert results[1]["metadata"].get("file") == "naive_div.txt"
