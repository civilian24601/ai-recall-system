import os
import shutil
import tempfile
import pytest
from unittest.mock import patch
import chromadb

import scripts.index_codebase as index_mod

@pytest.fixture
def setup_test_dir():
    """
    Creates a temporary directory with:
      1) a small python file with a function
      2) a small markdown file
    We yield the path, then remove it after test.
    """
    tmp_dir = tempfile.mkdtemp(prefix="index_codebase_test_")

    # Create a .py file
    pyfile = os.path.join(tmp_dir, "example_test.py")
    with open(pyfile, "w") as f:
        f.write("def test_func():\n    print('Hello from test_func')\n")

    # Create a .md file
    mdfile = os.path.join(tmp_dir, "example.md")
    with open(mdfile, "w") as f:
        f.write("# Example Markdown\nThis is a test markdown file.\n")

    yield tmp_dir

    # cleanup
    shutil.rmtree(tmp_dir)

@pytest.fixture
def codebase_test_client():
    """
    Creates a Chroma client, returning a test collection named 'project_codebase_test'.
    We'll remove docs after the test.
    """
    client = chromadb.PersistentClient(path=index_mod.CHROMA_DB_PATH)
    coll = client.get_or_create_collection(name="project_codebase_test")
    yield coll
    # Teardown => remove docs
    results = coll.get(limit=9999)
    if "ids" in results and results["ids"]:
        coll.delete(ids=results["ids"])

@patch.object(index_mod, "ROOT_DIRS", new=[])
@patch.object(index_mod, "COLLECTION_NAME", new="project_codebase_test")
def test_index_codebase_one_shot(setup_test_dir, codebase_test_client):
    """
    We monkeypatch 'ROOT_DIRS' to only index the ephemeral directory,
    then run index_codebase(), check that some chunks were added to 'project_codebase_test'.
    We do NOT test watchers here.
    """
    index_mod.ROOT_DIRS.append(setup_test_dir)

    # Call the main function
    index_mod.index_codebase()

    # Now check that we have some docs in the test collection
    results = codebase_test_client.get(limit=9999)
    docs = results.get("documents", [])
    assert len(docs) > 0, "Expected at least one chunk from the ephemeral test dir."

    # Optionally check that we have doc IDs referencing example_test.py or example.md
    # For instance:
    doc_ids = results.get("ids", [])
    matched_py = [did for did in doc_ids if "example_test.py" in did]
    matched_md = [did for did in doc_ids if "example.md" in did]
    assert matched_py, "Expected some doc_id referencing 'example_test.py'"
    assert matched_md, "Expected some doc_id referencing 'example.md'"
