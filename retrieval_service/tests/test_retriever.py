import pytest
import numpy as np
import json
from pathlib import Path
from unittest.mock import patch
from retriever import Retriever

@pytest.fixture
def sample_docs(tmp_path):
    docs = [
        {"id": 1, "text": "Document one text."},
        {"id": 2, "text": "Document two text."},
        {"id": 3, "text": "Document three text."}
    ]
    docstore_path = tmp_path / "docstore.json"
    docstore_path.write_text(json.dumps(docs), encoding="utf-8")
    return docs, str(docstore_path)

@pytest.fixture
def sample_index_dir(tmp_path):
    return str(tmp_path)

@pytest.fixture
def dummy_index(sample_index_dir):
    # Create a dummy FAISS index of dimension 4 and save it
    import faiss
    dim = 4
    index = faiss.IndexFlatIP(dim)
    
    vectors = np.array([
        [0.1, 0.2, 0.3, 0.4],
        [0.4, 0.3, 0.2, 0.1],
        [0.5, 0.5, 0.5, 0.5]
    ], dtype=np.float32)
    index.add(vectors)
    faiss.write_index(index, str(Path(sample_index_dir) / "index.faiss"))
    meta = {"dim": dim}
    (Path(sample_index_dir) / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return sample_index_dir

def mock_encode(self, texts, **kwargs):
    # Return fixed dimension embeddings matching FAISS index dimension (4)
    # One embedding vector per text element
    return np.array([[0.1, 0.2, 0.3, 0.4] for _ in texts], dtype=np.float32)

def test_load_documents(sample_docs, dummy_index):
    docs, docstore_path = sample_docs
    retriever = Retriever("BAAI/bge-m3", dummy_index, docstore_path, top_k=2)
    assert retriever.documents == docs

def test_load_index(sample_docs, dummy_index):
    docstore_path = sample_docs[1]
    retriever = Retriever("BAAI/bge-m3", dummy_index, docstore_path, top_k=2)
    assert retriever.index is not None
    assert retriever.dim == 4

@patch("retriever.SentenceTransformer.encode", new=mock_encode)
def test_search_results(sample_docs, dummy_index):
    docstore_path = sample_docs[1]
    retriever = Retriever("BAAI/bge-m3", dummy_index, docstore_path, top_k=2)
    results = retriever.search("Document")
    assert isinstance(results, list)
    assert len(results) <= 2
    for res in results:
        assert "score" in res
        assert "document" in res
