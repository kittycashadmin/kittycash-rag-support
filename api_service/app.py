from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
from pydantic import BaseModel
from config import RETRIEVAL_SERVICE_URL, GENERATION_SERVICE_URL, TOP_K

app = FastAPI()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api_server")

class QueryRequest(BaseModel):
    user_query: str

@app.get("/health")
async def health_check():
    return {"status": "API server running"}

@app.post("/query/")
async def query_endpoint(req: QueryRequest):
    user_query = req.user_query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="user_query is required")

    logger.info(f"Received user query: {user_query}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            retrieval_resp = await client.get(
                f"{RETRIEVAL_SERVICE_URL}/search/",
                params={"query": user_query},
            )
            retrieval_resp.raise_for_status()
            context_docs = retrieval_resp.json().get("results", [])[:TOP_K]
            logger.info(f"Retrieved {len(context_docs)} documents from retrieval service.")
            gen_payload = {
                "user_query": user_query,
                "context": [doc["document"] for doc in context_docs]
            }
            logger.info(f"Sending to generation service: {gen_payload}")
            generation_resp = await client.post(
                f"{GENERATION_SERVICE_URL}/generate/",
                json=gen_payload,
            )
            generation_resp.raise_for_status()
            answer = generation_resp.json().get("answer", "")
            logger.info(f"Generated answer length: {len(answer)}")

            return {"answer": answer}

    except httpx.RequestError as e:
        logger.error(f"Request error: {e} - {e.request.url if e.request else ''}")
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)