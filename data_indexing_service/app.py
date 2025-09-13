from fastapi import FastAPI, HTTPException, Query
from embedder import Embedder
from indexer import Indexer
from documents import load_kb_files, load_docstore, save_docstore
from config import EMBED_MODEL, INDEX_DIR, KB_FILES_DIR
import numpy as np
from pathlib import Path
import json

app = FastAPI(
    title="Kitty Cash Data/Indexing Service",
    description="Manages document loading, embeddings, and FAISS index with versioning.",
    version="1.2.0"
)

embedder = Embedder(EMBED_MODEL)
indexer = Indexer(INDEX_DIR)
documents = []
current_version = None

def get_next_version():
    global current_version
    try:
        versions = sorted(Path(INDEX_DIR).glob("*.meta.json"))
        if not versions:
            current_version = "v1"
            return current_version
        latest_meta_path = versions[-1]
        meta = json.loads(latest_meta_path.read_text())
        last_version = meta["version"]
        num = int(last_version.replace("v", ""))
        current_version = f"v{num + 1}"
        return current_version
    except FileNotFoundError:
        current_version = "v1"
        return current_version

@app.on_event("startup")
def startup_event():
    global documents, current_version
    try:
        meta = indexer.load_latest()
        documents = load_docstore()
        current_version = meta["version"]
        print(f"Loaded latest index: {meta['version']}")
    except FileNotFoundError:
        documents = load_kb_files(KB_FILES_DIR)
        if not documents:
            raise RuntimeError("Knowledge base is empty. Please add KB files.")
        texts = [doc["text"] for doc in documents]
        embeddings = embedder.encode(texts)
        indexer.build(embeddings)
        version = get_next_version()
        indexer.save(version, len(documents))
        save_docstore(documents)
        print(f"Created initial index: {version}")

@app.get("/health")
def health_check():
    return {"status": "Data/Indexing Service is running"}

@app.get("/index/add")
def add_to_index(kb_file: str = Query(None, description="KB file path added")):
    global documents

    if kb_file:
        kb_path = Path(kb_file)
        if not kb_path.exists():
            full_path = Path(KB_FILES_DIR) / kb_file
            if not full_path.exists():
                raise HTTPException(status_code=400, detail=f"KB file not found: {kb_file}. Checked {kb_path} and {full_path}")
            kb_path = full_path
        new_docs = load_kb_files(kb_path.parent, kb_path.name)
    else:
        new_docs = load_kb_files(KB_FILES_DIR)

    existing_texts = {doc["text"] for doc in documents}
    fresh_docs = [doc for doc in new_docs if doc["text"] not in existing_texts]

    if not fresh_docs:
        return {"message": "No new KB documents to add.", "total_docs": len(documents)}
    
    texts = [doc["text"] for doc in fresh_docs]
    embeddings = embedder.encode(texts)   
    print(f"Adding embeddings with shape: {embeddings.shape}")
    
    indexer.add(embeddings)  
    print(f"Index contains {indexer.index.ntotal} vectors after adding.")

    documents.extend(fresh_docs)
    version = get_next_version()
    indexer.save(version, len(documents))
    save_docstore(documents)

    return {
        "message": f"Added {len(fresh_docs)} new KB documents. Index version: {version}",
        "total_docs": len(documents)
    }

@app.get("/index/status")
def index_status():
    try:
        meta = indexer.load_latest()
        kb_files_count = len(list(Path(KB_FILES_DIR).glob("*.txt")))
        return {
            "status": "Index loaded",
            "version": meta["version"],
            "dimensions": meta["dim"],
            "total_documents": meta["doc_count"],
            "kb_files_count": kb_files_count
        }
    except FileNotFoundError:
        return {"status": "Index not found", "kb_files_count": 0}