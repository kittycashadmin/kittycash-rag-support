# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from imagebind.models import imagebind_model
from imagebind import data


class Embedder:
    def __init__(self, model_name: str):
        self.model_name = model_name.lower()

        if "bge" in self.model_name: 
            print(f"Using SentenceTransformer model: {model_name}")
            self.model = SentenceTransformer(model_name)

        elif "imagebind" in self.model_name:
            print(f"Using ImageBind model: {model_name}")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = imagebind_model.imagebind_huge(pretrained=True)
            self.model.eval()
            self.model.to(self.device)

        else:
            raise ValueError(f"Unknown model_name: {model_name}")

    def encode(self, texts):
        if not texts or len(texts) == 0:
            print("called with empty texts")
            return np.zeros((0, 1024), dtype="float32")  

        if "bge" in self.model_name:
            return self.model.encode(
                texts,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            ).astype("float32")

        elif "imagebind" in self.model_name:
            inputs = {"text": data.load_and_transform_text(texts, self.device)}
            with torch.no_grad():
                embeddings = self.model(inputs)
            emb = embeddings["text"].cpu().numpy().astype("float32")
            return emb.reshape(len(texts), -1)

        else:
            raise ValueError(f"Unknown model_name: {self.model_name}")
