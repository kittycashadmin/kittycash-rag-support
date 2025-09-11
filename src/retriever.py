from typing import List, Dict
from .embedder import Embedder
from .vector_store import VectorStore

class Retriever:
    def __init__(self, embed_model: str, vector_store: VectorStore, documents: List[Dict]):
        self.embedder = Embedder(embed_model)
        self.vector_store = vector_store
        self.documents = documents  

    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        qv = self.embedder.encode([query])
        scores, idx = self.vector_store.search(qv, k)
        hits = []
        for rank, doc_idx in enumerate(idx[0]):
            if doc_idx < 0 or doc_idx >= len(self.documents):
                continue
            doc = self.documents[doc_idx]
            hits.append({
                "rank": rank + 1,
                "score": float(scores[0][rank]),
                **doc
            })
        return hits
