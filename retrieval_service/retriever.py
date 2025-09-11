from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from pathlib import Path
import json

class Retriever:
    def __init__(self, embed_model: str, index_dir: str, docstore_path: str, top_k: int = 3):
        self.embedder = SentenceTransformer(embed_model)
        self.top_k = top_k
        self.index_dir = Path(index_dir)
        self.docstore_path = Path(docstore_path)
        self.index = None
        self.dim = None
        self.documents = self.load_documents()
        self.load_index()

    def load_index(self):
        index_path = self.index_dir / "index.faiss"
        meta_path = self.index_dir / "meta.json"
        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError("FAISS index files not found")
        self.index = faiss.read_index(str(index_path))
        self.dim = json.loads(meta_path.read_text())["dim"]

    def load_documents(self):
        if not self.docstore_path.exists():
            return []
        with open(self.docstore_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def search(self, query: str):
        query_embedding = self.embedder.encode([query], normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding, self.top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.documents):
                continue
            doc = self.documents[idx]
            results.append({"score": float(score), "document": doc})
        return results
