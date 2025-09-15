from fastapi import FastAPI, HTTPException, Request
import httpx 
import logging 
from pydantic import BaseModel 
from config import RETRIEVAL_SERVICE_URL, GENERATION_SERVICE_URL, TOP_K

app = FastAPI()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("support_server")


@app.get("/health")
async def health_check():
    return {"status": "API server running"}

@app.post("/support/chat")
async def support_chat(request: Request):
    data = await request.json()
    user_message = data.get("message")
    user_id = data.get("user_id")

    if not user_message or not user_id:
        raise HTTPException(status_code=400, detail="Missing 'message' or 'user_id'")

    logger.info(f"Received message from user {user_id}: {user_message}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            retrieval_resp = await client.get(
                f"{RETRIEVAL_SERVICE_URL}/search/",
                params={"query": user_message},
            )
            retrieval_resp.raise_for_status()
            context_docs = retrieval_resp.json().get("results", [])[:TOP_K]

            logger.info(f"Retrieved {len(context_docs)} documents from retrieval service.")
            context = [doc["document"] for doc in context_docs]
            gen_payload = {
                "user_query": user_message,
                "context": context
            }

            logger.info(f"Sending context to generation service.")
            generation_resp = await client.post(
                f"{GENERATION_SERVICE_URL}/generate/",
                json=gen_payload
            )
            generation_resp.raise_for_status()
            answer = generation_resp.json().get("answer", "")

            logger.info(f"Generated answer for user {user_id}")

            return {
                "status": "success",
                "responses": [
                    {
                        "type": "text",
                        "content": answer
                    }
                ]
            }

    except httpx.RequestError as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
