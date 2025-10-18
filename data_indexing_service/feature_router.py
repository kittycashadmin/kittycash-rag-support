# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import numpy as np
from embedder import Embedder
from config import EMBED_MODEL


class FeatureRouter:

    def __init__(self):
        self.embedder = Embedder(EMBED_MODEL)
        self.features = self._load_features()
        self.feature_embeddings = self._encode_features()

    def _load_features(self):
        return [
            {
                "id": 1,
                "name": "Account & Authentication",
                "description": "Signup, login, password reset, account creation, access control",
                "keywords": ["signup", "login", "password", "account", "status", "auth"]
            },
            {
                "id": 2,
                "name": "User Profile Management",
                "description": "Profile update, photo upload, user information changes",
                "keywords": ["profile", "photo", "update", "name", "picture"]
            },
            {
                "id": 3,
                "name": "Groups & Invitations",
                "description": "Group creation, invitation, members, group rules",
                "keywords": ["group", "invite", "member", "team"]
            },
            {
                "id": 4,
                "name": "Payments & Payouts",
                "description": "Payment setup, fees, transactions, refund, payout details",
                "keywords": ["payment", "payout", "refund", "transaction", "fee", "money"]
            },
            {
                "id": 5,
                "name": "App Usage & Support",
                "description": "Help, troubleshooting, app guidance, general usage",
                "keywords": ["help", "support", "troubleshoot", "error"]
            }
        ]

    def _encode_features(self):
        texts = [f"{f['name']} {f.get('description', '')}" for f in self.features]
        return self.embedder.encode(texts)

    def _keyword_match(self, text: str):
        text_lower = text.lower()
        for f in self.features:
            for kw in f.get("keywords", []):
                if kw.lower() in text_lower:
                    return {
                        "feature_id": f["id"],
                        "feature_name": f["name"],
                        "confidence": 1.0,
                        "source": "keyword"
                    }
        return None

    def _embedding_match(self, text: str):
        q_emb = self.embedder.encode([text])
        sims = np.dot(q_emb, self.feature_embeddings.T)[0]
        idx = int(np.argmax(sims))
        score = float(sims[idx])
        feature = self.features[idx]
        return {
            "feature_id": feature["id"],
            "feature_name": feature["name"],
            "confidence": score,
            "source": "embedding"
        }

    def detect_feature(self, text: str):
        kw = self._keyword_match(text)
        if kw:
            return kw
        emb = self._embedding_match(text)
        if emb["confidence"] >= 0.45:
            return emb
        return None
