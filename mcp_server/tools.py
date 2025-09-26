# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import httpx
import logging
from pathlib import Path
from config import RETRIEVAL_SERVICE_URL, GENERATION_SERVICE_URL, INDEXING_SERVICE_URL, TOP_K

logger = logging.getLogger("tools")

async def retriever_tool(payload: dict):
    query = payload.get("query")
    if not query:
        logger.warning("Missing 'query' in payload")
        return {"error": "Missing 'query'", "results": []}

    logger.info(f"Calling retrieval service with query: {query!r}")
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RETRIEVAL_SERVICE_URL}/search/", params={"query": query})
        resp.raise_for_status()
        results = resp.json().get("results", [])[:TOP_K]
    logger.info(f"Retrieval service returned {len(results)} results")
    return {"results": results}


async def generator_tool(payload: dict):
    user_query = payload.get("user_query")
    context = payload.get("context", [])

    if not user_query:
        logger.warning("Missing 'user_query' in payload")
        return {"error": "Missing 'user_query'", "answer": ""}

    logger.info(f"Calling generation service with user_query={user_query!r} context_len={len(context)}")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GENERATION_SERVICE_URL}/generate/",
            json={"user_query": user_query, "context": context[:TOP_K]},
            timeout=120.0,
        )
        resp.raise_for_status()
        gen_json = resp.json()
    logger.info(f"Generation service response keys: {list(gen_json.keys()) if isinstance(gen_json, dict) else 'non-dict'}")
    return gen_json if isinstance(gen_json, dict) else {"answer": str(gen_json)}


async def indexer_tool(payload: dict):
    kb_file = payload.get("kb_file")
    if not kb_file:
        logger.warning("Missing 'kb_file' in payload")
        return {"error": "Missing 'kb_file'"}

    kb_path = Path(kb_file)
    if not kb_path.exists():
        logger.error(f"File not found: {kb_path}")
        return {"error": f"File not found: {kb_file}"}

    logger.info(f"Uploading kb_file={kb_file!r} to indexing service")
    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(kb_path, "rb") as f:
            files = {"file": (kb_path.name, f, "text/plain")}
            resp = await client.post(f"{INDEXING_SERVICE_URL}/index/add", files=files)

        resp.raise_for_status()
        result = resp.json()

    logger.info(f"Indexer response: {result}")
    return result if isinstance(result, dict) else {"result": result}
