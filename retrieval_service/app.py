# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

from fastapi import FastAPI, HTTPException
from retriever import Retriever
from config import EMBED_MODEL, INDEX_DIR, DOCSTORE_PATH, TOP_K
from feature_router import FeatureRouter 
feature_router = FeatureRouter()

app = FastAPI(
    title="Kitty Cash Retrieval Service",
    description="Searches FAISS index to retrieve relevant documents for user queries.",
    version="1.0.0"
)

retriever = Retriever(EMBED_MODEL, INDEX_DIR, DOCSTORE_PATH, TOP_K)

@app.get("/retrieval/service/health")
def health_check():
    return {"status": "Retrieval Service running"}

@app.get("/retrieval/search/query")
def search(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    results = retriever.search(query, mode="generator")
    return {"query": query, "results": results}


@app.get("/retrieval/search/kcadmin")
def search_admin(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    results = retriever.search(query, mode="admin")
    return results


'''@app.get("/retrieval/features/list")
def list_features():
    return {"features": feature_router.features}'''

