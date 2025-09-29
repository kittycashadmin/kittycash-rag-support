# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import json
from pathlib import Path
from typing import List, Dict, Any
import faiss
import numpy as np
from embedder import Embedder   
from config import EMBED_MODEL, INDEX_DIR, DOCSTORE_PATH, TOP_K


class Retriever:
    def __init__(self, embed_model: str, index_dir: str, docstore_path: str, top_k: int = 3):
        self.embedder = Embedder(embed_model)
        self.top_k = int(top_k)
        self.index_dir = Path(index_dir)
        self.docstore_path = Path(docstore_path)
        self.index = None
        self.dim = None
        self.documents: List[Dict[str, Any]] = self.load_documents()
        self.load_index()

    def load_index(self):
        versions = sorted(self.index_dir.glob("*.meta.json"))
        if not versions:
            raise FileNotFoundError(f"No index versions found in {self.index_dir}")

        latest_meta_path = versions[-1]
        meta = json.loads(latest_meta_path.read_text())
        version = meta["version"]

        index_path = self.index_dir / f"{version}.index"
        if not index_path.exists():
            raise FileNotFoundError(f"Index file for version {version} not found at {index_path}")
        self.index = faiss.read_index(str(index_path))
        self.dim = meta["dim"]
        print(f"[Retriever] Loaded latest index version {version} with dimension {self.dim}")

    def load_documents(self) -> List[Dict[str, Any]]:
        if not self.docstore_path.exists():
            print(f"No docstore found at {self.docstore_path}")
            return []
        with open(self.docstore_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def search(self, query: str):
        if not query or self.index is None:
            return []

        query_embedding = self.embedder.encode([query])

        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype("float32")
        if self.dim is not None and query_embedding.shape[1] != self.dim:
            raise RuntimeError(f"Embedding dimension mismatch: query {query_embedding.shape[1]} vs index {self.dim}")
        k = max(1, int(self.top_k))
        scores, indices = self.index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            results.append({"score": float(score), "document": doc})

        return results
