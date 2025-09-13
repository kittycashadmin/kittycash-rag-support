from pathlib import Path
import json
import pytest
from documents import load_knowledge_base, save_docstore, load_docstore
from unittest.mock import patch, mock_open

def test_load_knowledge_base(tmp_path):
    kb_content = "Doc 1 text\n---\nDoc 2 text"
    kb_path = tmp_path / "knowledge_base.txt"
    kb_path.write_text(kb_content, encoding="utf-8")

    with patch("documents.KB_PATH", kb_path):
        docs = load_knowledge_base()
    assert len(docs) == 2
    assert docs[0]["text"] == "Doc 1 text"

def test_save_and_load_docstore(tmp_path):
    docs = [{"id": 1, "text": "Sample text"}]
    docstore_path = tmp_path / "docstore.json"

    with patch("documents.DOCSTORE_PATH", docstore_path):
        save_docstore(docs)
        loaded_docs = load_docstore()
    assert loaded_docs == docs

def test_load_docstore_file_missing(tmp_path):
    docstore_path = tmp_path / "docstore.json"
    with patch("documents.DOCSTORE_PATH", docstore_path):
        result = load_docstore()
    assert result == []
