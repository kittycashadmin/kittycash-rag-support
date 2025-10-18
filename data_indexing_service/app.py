# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from embedder import Embedder
from indexer import Indexer
from documents import load_kb_files, load_docstore, save_docstore
from config import EMBED_MODEL, INDEX_DIR, KB_FILES_DIR,ADMIN_API_URL
from pathlib import Path
import json
import httpx



app = FastAPI(
    title="Kitty Cash Data/Indexing Service",
    description="Manages document loading, embeddings, and FAISS index with versioning.",
    version="1.2.1"
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

@app.get("/indexing/service/health")
def health_check():
    return {"status": "Data/Indexing Service is running"}

@app.post("/indexing/index/add")
async def upload_and_index(file: UploadFile = File(...)):
    global documents
    kb_path = Path(KB_FILES_DIR) / file.filename
    kb_path.write_bytes(await file.read())

    new_docs = load_kb_files(KB_FILES_DIR, file.filename)  

    if not new_docs:
        raise HTTPException(status_code=400, detail="No valid QnA entries found in file")

    existing_texts = {doc["text"] for doc in documents}
    fresh_docs = [doc for doc in new_docs if doc["text"] not in existing_texts]
    if not fresh_docs:
        return {"message": "No new KB documents to add.", "total_docs": len(documents)}

    texts = [doc["text"] for doc in fresh_docs] 
    embeddings = embedder.encode(texts)
    indexer.add(embeddings)
    documents.extend(fresh_docs)

    version = get_next_version()
    indexer.save(version, len(documents))
    save_docstore(documents)


    summary = {}
    for d in fresh_docs:
        name = d.get("feature_name", "Uncategorized")
        summary[name] = summary.get(name, 0) + 1

    return {
        "message": f"Uploaded and indexed {len(fresh_docs)} documents. Index version: {version}",
        "by_feature": summary,
        "total_docs": len(documents)
    }

@app.get("/indexing/index/status")
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

"""
@app.post("/indexing/index/fetch-and-index")
def fetch_and_index():

    try:
        with httpx.Client(timeout=180.0) as client:
            resp = client.get(f"{ADMIN_API_URL}/admin/ai-chat/features/unindexed")
            resp.raise_for_status()
            data = resp.json().get("data", [])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch from admin: {e}")

    if not data:
        return {"message": "No new questions to index."}


    new_docs = []
    for q in data:
        text = f"{q['question']} | {q['answer']}"
        new_docs.append({
            "id": q["id"],
            "text": text,
            "feature_name": q["feature_name"],
            "source": "db"
        })

    texts = [d["text"] for d in new_docs]
    embeddings = embedder.encode(texts)
    indexer.add(embeddings)
    documents.extend(new_docs)

    version = get_next_version()
    indexer.save(version, len(documents))
    save_docstore(documents)

    ids = [d["id"] for d in new_docs]
    try:
        with httpx.Client(timeout=60.0) as client:
            client.post(f"{ADMIN_API_URL}/admin/ai-chat/features/mark-indexed", json={"question_ids": ids})
    except Exception as e:
        print(f" Failed to mark indexed: {e}")

    return {"message": f"Indexed {len(new_docs)} new questions.", "version": version}
"""