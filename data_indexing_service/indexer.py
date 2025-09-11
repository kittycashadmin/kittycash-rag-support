import faiss
import numpy as np
from pathlib import Path
import json


class Indexer:
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.dim = None

    def build(self, embeddings: np.ndarray, ids: np.ndarray):
       
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array [n, dim].")
        if len(embeddings) != len(ids):
            raise ValueError("Embeddings and IDs must have the same length.")

        self.dim = embeddings.shape[1]
        base_index = faiss.IndexFlatIP(self.dim)  
        self.index = faiss.IndexIDMap(base_index)
        self.index.add_with_ids(embeddings, ids.astype("int64"))

    def add(self, embeddings: np.ndarray, ids: np.ndarray):
        if self.index is None:
            raise RuntimeError("Index not built or loaded.")
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array [n, dim].")
        if len(embeddings) != len(ids):
            raise ValueError("Embeddings and IDs must have the same length.")
        self.index.add_with_ids(embeddings, ids.astype("int64"))

    def remove(self, ids: np.ndarray):
        if self.index is None:
            raise RuntimeError("Index not built or loaded.")
        ids = ids.astype("int64")
        sel = faiss.IDSelectorBatch(len(ids), faiss.swig_ptr(ids))
        self.index.remove_ids(sel)

    def save(self):
        if self.index is None:
            raise RuntimeError("No index to save.")
        faiss.write_index(self.index, str(self.index_dir / "index.faiss"))
        meta = {"dim": self.dim}
        (self.index_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    def load(self):
        index_path = self.index_dir / "index.faiss"
        meta_path = self.index_dir / "meta.json"
        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Index files not found in {self.index_dir}")

        self.index = faiss.read_index(str(index_path))
        self.dim = json.loads(meta_path.read_text())["dim"]
