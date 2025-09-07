from fastapi import FastAPI, HTTPException
from embedder import Embedder
from indexer import Indexer
from documents import load_knowledge_base, save_docstore, load_docstore
from config import EMBED_MODEL, INDEX_DIR
import numpy as np

app = FastAPI(
    title="Kitty Cash Data/Indexing Service",
    description="Manages document loading, embeddings, and FAISS index.",
    version="1.0.0"
)

embedder = Embedder(EMBED_MODEL)
indexer = Indexer(INDEX_DIR)
documents = []

THRESHOLD_RATIO = 0.4  

@app.on_event("startup")
def startup_event():
    global documents
    documents = load_knowledge_base()
    if not documents:
        raise RuntimeError("Knowledge base is empty. Please add documents.")

    texts = [doc["text"] for doc in documents]
    ids = np.array([int(doc["id"]) for doc in documents], dtype="int64")
    embeddings = np.array(embedder.encode(texts), dtype="float32")

    indexer.build(embeddings, ids)
    indexer.save()
    save_docstore(documents)


@app.get("/health")
def health_check():
    return {"status": "Data/Indexing Service is running"}


@app.get("/index/rebuild")
def rebuild_index():
    global documents
    documents = load_knowledge_base()
    if not documents:
        raise HTTPException(status_code=400, detail="No documents to index.")

    try:
        existing_docs = load_docstore()
        indexer.load()
        index_exists = True
    except FileNotFoundError:
        existing_docs = []
        index_exists = False


    if not index_exists:
        texts = [doc["text"] for doc in documents]
        ids = np.array([int(doc["id"]) for doc in documents], dtype="int64")
        embeddings = np.array(embedder.encode(texts), dtype="float32")

        indexer.build(embeddings, ids)
        indexer.save()
        save_docstore(documents)
        return {"message": "Index built from scratch", "document_count": len(documents)}


    existing_docs_map = {doc["id"]: doc["text"] for doc in existing_docs}
    changed_docs = [doc for doc in documents if existing_docs_map.get(doc["id"]) != doc["text"]]

    if not changed_docs:
        return {"message": "No new or updated documents found", "document_count": len(documents)}
    if len(changed_docs) / len(documents) >= THRESHOLD_RATIO:
        texts = [doc["text"] for doc in documents]
        ids = np.array([int(doc["id"]) for doc in documents], dtype="int64")
        embeddings = np.array(embedder.encode(texts), dtype="float32")

        indexer.build(embeddings, ids)
        indexer.save()
        save_docstore(documents)

        return {
            "message": "Index rebuilt due to large number of changes",
            "document_count": len(documents),
        }
    else:
        ids_to_update = np.array([int(doc["id"]) for doc in changed_docs], dtype="int64")
        texts_to_update = [doc["text"] for doc in changed_docs]
        new_embeddings = np.array(embedder.encode(texts_to_update), dtype="float32")

        indexer.remove(ids_to_update)
        indexer.add(new_embeddings, ids_to_update)

        updated_docs_map = {doc["id"]: doc for doc in documents}
        updated_docs = list(updated_docs_map.values())
        save_docstore(updated_docs)
        indexer.save()

        return {"message": "Index incrementally updated"}


@app.get("/index/status")
def index_status():
    try:
        indexer.load()
        return {"status": "Index loaded", "dimensions": indexer.dim}
    except FileNotFoundError:
        return {"status": "Index not found"}
