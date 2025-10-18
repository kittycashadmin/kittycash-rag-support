# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import json
from pathlib import Path
from typing import List, Dict, Any
import faiss
import numpy as np
from embedder import Embedder
from feature_router import FeatureRouter
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
        self.router = FeatureRouter()  # feature detection
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


    def search(self, query: str, mode: str = "generator") -> Any:
        if not query or self.index is None:
            return {"message": "No query or index not loaded"}

        detected = self.router.detect_feature(query)
        feature_name = detected.get("feature_name") if detected else None
        confidence = detected.get("confidence", 0.0) if detected else 0.0


        if feature_name:
            feature_docs = [d for d in self.documents if d.get("feature_name") == feature_name]
        else:
            feature_docs = self.documents

        if not feature_docs:
            return {
                "detected_feature": feature_name or "Unknown",
                "confidence": confidence,
                "top_matches": [],
                "all_feature_questions": []
            }

        query_emb = self.embedder.encode([query]).astype("float32")
        if query_emb.ndim == 1:
            query_emb = query_emb.reshape(1, -1)

        emb_list = [self.embedder.encode([d["text"]])[0] for d in feature_docs]
        emb_matrix = np.array(emb_list, dtype="float32")
        faiss.normalize_L2(emb_matrix)
        temp_index = faiss.IndexFlatIP(emb_matrix.shape[1])
        temp_index.add(emb_matrix)

        if mode == "generator":
            scores, indices = temp_index.search(query_emb, min(3, len(feature_docs)))
            top_matches = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(feature_docs):
                    continue
                doc = feature_docs[idx]
                parts = doc["text"].split("|")
                q = parts[0].strip()
                a = parts[1].strip() if len(parts) > 1 else ""
                top_matches.append({
                    "score": float(score),
                    "question": q,
                    "answer": a,
                    "feature_name": doc.get("feature_name", "Uncategorized")
                })
            return {
                "query": query,
                "detected_feature": feature_name or "Unknown",
                "confidence": confidence,
                "top_matches": top_matches
            }

        elif mode == "admin":
            all_feature_questions = []
            for doc in feature_docs:
                parts = doc["text"].split("|")
                q = parts[0].strip()
                a = parts[1].strip() if len(parts) > 1 else ""
                all_feature_questions.append({"id": doc.get("id"),"question": q, "answer": a})

            scores, indices = temp_index.search(query_emb, min(self.top_k, len(feature_docs)))
            top_matches = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx >= len(feature_docs):
                    continue
                doc = feature_docs[idx]
                parts = doc["text"].split("|")
                q = parts[0].strip()
                a = parts[1].strip() if len(parts) > 1 else ""
                top_matches.append({
                    "id": doc.get("id"),
                    "score": float(score),
                    "question": q,
                    "answer": a,
                    "feature_name": doc.get("feature_name", "Uncategorized")
                })

            return {
                "query": query,
                "detected_feature": feature_name or "Unknown",
                "confidence": confidence,
                "top_matches": top_matches,
                "all_feature_questions": all_feature_questions
            }

        else:
            raise ValueError(f"Invalid search mode: {mode}")
