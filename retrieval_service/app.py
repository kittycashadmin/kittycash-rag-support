from fastapi import FastAPI, HTTPException
from retriever import Retriever
from config import EMBED_MODEL, INDEX_DIR, DOCSTORE_PATH, TOP_K

app = FastAPI(
    title="Kitty Cash Retrieval Service",
    description="Searches FAISS index to retrieve relevant documents for user queries.",
    version="1.0.0"
)

retriever = Retriever(EMBED_MODEL, INDEX_DIR, DOCSTORE_PATH, TOP_K)

@app.get("/health")
def health_check():
    return {"status": "Retrieval Service running"}

@app.get("/search/")
def search(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    results = retriever.search(query)
    return {"query": query, "results": results}
