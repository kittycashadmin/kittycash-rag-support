import faiss
import numpy as np
from pathlib import Path
import json

class VectorStore:
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.dim = None

    def build(self, embeddings: np.ndarray):
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be a 2D array [n, dim].")
        self.dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(embeddings)

    def search(self, query_vec: np.ndarray, k: int = 5):
        if self.index is None:
            raise RuntimeError("Vector index not loaded or built.")
        scores, idx = self.index.search(query_vec, k)
        return scores, idx

    def save(self):
        if self.index is None:
            raise RuntimeError("No index to save.")
        faiss.write_index(self.index, str(self.index_dir / "index.faiss"))
        meta = {"dim": self.dim}
        (self.index_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

    def load(self):
        index_path = self.index_dir / "index.faiss"
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        self.index = faiss.read_index(str(index_path))
        meta_path = self.index_dir / "meta.json"
        if meta_path.exists():
            import json
            self.dim = json.loads(meta_path.read_text())["dim"]
