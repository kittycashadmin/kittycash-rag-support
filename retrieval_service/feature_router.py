# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import numpy as np
from sentence_transformers import SentenceTransformer

class FeatureRouter:
    """
    Hybrid feature detection:
      1. Keyword-based matching (fast, interpretable)
      2. Embedding similarity fallback (semantic)
    Returns: {"feature_id", "feature_name", "confidence", "source"}
    """

    def __init__(self):
        self.embedder = SentenceTransformer("BAAI/bge-m3")

        self.features = [
            {"id": 1, "name": "Account & Authentication"},
            {"id": 2, "name": "User Profile Management"},
            {"id": 3, "name": "Groups & Invitations"},
            {"id": 4, "name": "Payments & Payouts"},
            {"id": 5, "name": "App Usage & Support"}
        ]

        self.feature_keywords = {
            "Account & Authentication": [
                "account", "login", "signup", "register", "password",
                "authentication", "sign in", "sign up", "security", "access"
            ],
            "User Profile Management": [
                "profile", "settings", "update info", "personal details", "avatar", "photo", "user info"
            ],
            "Groups & Invitations": [
                "group", "member", "invitation", "join", "create group",
                "kitty", "members", "team", "participants"
            ],
            "Payments & Payouts": [
                "payment", "payout", "refund", "transaction", "bill",
                "transfer", "add card", "withdraw", "fee"
            ],
            "App Usage & Support": [
                "help", "support", "how to", "issue", "troubleshoot",
                "bug", "guide", "usage", "contact", "kittycash"
            ]
        }


        self.feature_embeddings = self._compute_feature_embeddings()

    def _compute_feature_embeddings(self):
        refs = {}
        for f in self.features:
            f_name = f["name"]
            words = " ".join(self.feature_keywords.get(f_name, []))
            combined = f_name + " " + words
            emb = self.embedder.encode([combined], normalize_embeddings=True)[0]
            refs[f_name] = emb
        return refs

    def detect_feature(self, text: str):
        text_l = text.lower()


        for f in self.features:
            f_name = f["name"]
            for kw in self.feature_keywords.get(f_name, []):
                if kw in text_l:
                    return {
                        "feature_id": f["id"],
                        "feature_name": f_name,
                        "confidence": 0.95,
                        "source": "keyword"
                    }

        text_emb = self.embedder.encode([text], normalize_embeddings=True)
        sims = {}
        for f_name, emb in self.feature_embeddings.items():
            sim = float(np.dot(text_emb[0], emb))
            sims[f_name] = sim

        best_feature = max(sims, key=sims.get)
        confidence = sims[best_feature]

        if confidence < 0.55:
            return None

        f = next(f for f in self.features if f["name"] == best_feature)
        return {
            "feature_id": f["id"],
            "feature_name": f["name"],
            "confidence": round(confidence, 3),
            "source": "embedding"
        }
