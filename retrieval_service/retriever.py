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

    def load_documents(self):
        if not self.docstore_path.exists():
            print(f"No docstore found at {self.docstore_path}")
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