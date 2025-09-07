import pytest
from embedder import Embedder

def test_embedding_size():
    texts = ["This is a test.", "Another testing sentence."]
    embedder = Embedder("BAAI/bge-m3")
    embeddings = embedder.encode(texts)
    assert embeddings.shape[0] == len(texts)
    assert embeddings.shape[1] > 0  # Some positive dimensionality

def test_embedding_normalization():
    texts = ["Normalize test."]
    embedder = Embedder("BAAI/bge-m3")
    embeddings = embedder.encode(texts)
    # Check that each embedding vector length is approximately 1 (normalized)
    for vector in embeddings:
        length = (vector**2).sum()**0.5
        assert abs(length - 1.0) < 1e-3
