import numpy as np
import pytest
from pathlib import Path
from indexer import Indexer

@pytest.fixture
def sample_embeddings():
    return np.array([
        [0.1, 0.2, 0.3, 0.4],
        [0.4, 0.3, 0.2, 0.1],
        [0.5, 0.5, 0.5, 0.5]
    ], dtype=np.float32)

@pytest.fixture
def index_dir(tmp_path):
    return tmp_path

def test_build_save_load_index(sample_embeddings, index_dir):
    indexer = Indexer(str(index_dir))
    indexer.build(sample_embeddings)
    assert indexer.index is not None
    assert indexer.dim == sample_embeddings.shape[1]

    indexer.save()
    assert (index_dir / "index.faiss").exists()
    assert (index_dir / "meta.json").exists()

    indexer2 = Indexer(str(index_dir))
    indexer2.load()
    assert indexer2.index is not None
    assert indexer2.dim == sample_embeddings.shape[1]

    query_vec = np.array([[0.1, 0.2, 0.3, 0.4]], dtype=np.float32)
    distances, indices = indexer2.index.search(query_vec, 2)
    assert indices.shape == (1, 2)
