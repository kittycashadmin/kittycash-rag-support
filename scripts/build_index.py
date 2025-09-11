from pathlib import Path
import numpy as np

from src.embedder import Embedder
from src.vector_store import VectorStore
from src.utils import load_knowledge_base, save_docstore
from src.config import EMBED_MODEL, INDEX_DIR, DOCSTORE_PATH, KB_PATH

def main():
    print("Loading knowledge base...")
    docs = load_knowledge_base(KB_PATH)
    if not docs:
        raise SystemExit("No documents found in knowledge_base.txt")

    print(f"Loaded {len(docs)} docs. Embedding with {EMBED_MODEL} ...")
    embedder = Embedder(EMBED_MODEL)
    corpus = [d["text"] for d in docs]
    embs = embedder.encode(corpus)

    print("Building FAISS index...")
    vs = VectorStore(INDEX_DIR)
    vs.build(embs)
    vs.save()

    print("Saving docstore...")
    save_docstore(DOCSTORE_PATH, docs)

    print("Done. Index is ready.")

if __name__ == "__main__":
    main()
