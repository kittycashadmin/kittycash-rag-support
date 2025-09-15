import faiss
import numpy as np
from pathlib import Path
import json
from datetime import datetime

class Indexer:
    def __init__(self, index_dir: str):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.dim = None

    def build(self, embeddings: np.ndarray):
        print(f"Building new index with shape: {embeddings.shape}")
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be 2D array [n, dim].")
        self.dim = embeddings.shape[1]
        num_vectors = embeddings.shape[0]

        if num_vectors < 100:  
            self.index = faiss.IndexFlatIP(self.dim)
            self.index.add(embeddings)
            print(f"Built Flat index with {self.index.ntotal} vectors.")
        else:
            nlist = min(100, num_vectors // 4) #change it to dynamic dont fix the centroids
            quantizer = faiss.IndexFlatIP(self.dim)
            self.index = faiss.IndexIVFFlat(quantizer, self.dim, nlist, faiss.METRIC_INNER_PRODUCT)
            self.index.train(embeddings)
            self.index.add(embeddings)
            print(f"[Indexer] Built IVF index with nlist={nlist} and {self.index.ntotal} vectors.")

        return self.index

    def add(self, embeddings: np.ndarray):
        if self.index is None:
            raise RuntimeError("Index not loaded. Load or build first.")
        print(f"[Indexer] Adding {embeddings.shape[0]} embeddings to existing index.")
        if isinstance(self.index, faiss.IndexIVFFlat) and not self.index.is_trained:
            self.index.train(embeddings)
        self.index.add(embeddings)
        print(f"[Indexer] Index now contains {self.index.ntotal} vectors.")
        return self.index

    def save(self, version: str, docs_added: int):
        if self.index is None:
            raise RuntimeError("No index to save.")

        index_path = self.index_dir / f"{version}.index"
        faiss.write_index(self.index, str(index_path))
        print(f"[Indexer] Saved FAISS index to {index_path}")
        print(f"[Indexer] Index file size: {index_path.stat().st_size} bytes")

        meta = {
            "version": version,
            "dim": self.dim,
            "doc_count": docs_added,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        meta_path = self.index_dir / f"{version}.meta.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print(f"[Indexer] Saved metadata to {meta_path}")

    def load(self, version: str):
        index_path = self.index_dir / f"{version}.index"
        meta_path = self.index_dir / f"{version}.meta.json"
        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"Index files for {version} not found in {self.index_dir}")
        self.index = faiss.read_index(str(index_path))
        meta = json.loads(meta_path.read_text())
        self.dim = meta["dim"]
        print(f"[Indexer] Loaded index version {version} with dimension {self.dim}")
        return meta

    def load_latest(self):
        versions = sorted(self.index_dir.glob("*.meta.json"))
        if not versions:
            raise FileNotFoundError(f"No index versions found in {self.index_dir}")

        latest_meta_path = versions[-1]
        meta = json.loads(latest_meta_path.read_text())
        version = meta["version"]

        index_path = self.index_dir / f"{version}.index"
        self.index = faiss.read_index(str(index_path))
        self.dim = meta["dim"]
        print(f"Loaded latest index version {version} with dimension {self.dim}")
        return meta