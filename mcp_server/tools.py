# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import httpx
import logging
from pathlib import Path
from config import (
    RETRIEVAL_SERVICE_URL,
    GENERATION_SERVICE_URL,
    INDEXING_SERVICE_URL,
    TOP_K
)

logger = logging.getLogger("tools")

timeout_config = httpx.Timeout(connect=600.0, read=600.0, write=600.0, pool=None)




async def retriever_tool(payload: dict):
    query = payload.get("query")
    if not query:
        logger.warning("Missing 'query' in payload")
        return {"error": "Missing 'query'", "results": []}

    logger.info(f"Calling retrieval service with query: {query!r}")
    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            resp = await client.get(
                f"{RETRIEVAL_SERVICE_URL}/retrieval/search/query", params={"query": query}
            )
            resp.raise_for_status()

            try:
                response_json = resp.json()
            except Exception as e:
                logger.exception("Failed to decode JSON response from retrieval service")
                return {"error": "Invalid JSON response from retrieval service", "results": []}

            results_dict = response_json.get("results", {})
            results_list = results_dict.get("top_matches", [])

            if not isinstance(results_list, list):
                logger.error(f"Unexpected results format (not a list): {results_list}")
                results_list = []

            results = results_list[:TOP_K]

        logger.info(f"Retrieval service returned {len(results)} results")
        return {"results": results}

    except httpx.RequestError as e:
        logger.error(f"HTTP request error while calling retrieval service: {e}")
        return {"error": str(e), "results": []}
    except Exception as e:
        logger.exception(f"Unexpected error in retriever_tool: {e}")
        return {"error": str(e), "results": []}





async def retriever_admin_search_tool(payload: dict):
    query = payload.get("query")
    if not query:
        logger.warning("Missing 'query' in payload")
        return {"error": "Missing 'query'"}

    logger.info(f"Calling retrieval admin search with query: {query!r}")
    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            resp = await client.get(f"{RETRIEVAL_SERVICE_URL}/retrieval/search/kcadmin", params={"query": query})

            resp.raise_for_status()
            results = resp.json()
        logger.info(f"Retrieval admin search returned keys: {list(results.keys()) if isinstance(results, dict) else 'non-dict'}")
        return results
    except httpx.ReadTimeout:
        logger.error(f"Retriever admin search timed out after {timeout_config.read}s for query: {query}")
        return {"error": f"Retriever timeout for query='{query}'"}
    except Exception as e:
        logger.exception(f"Retriever admin search failed: {e}")
        return {"error": str(e)}

"""
async def retriever_features_tool():
    logger.info("Calling retrieval service to list features")
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        resp = await client.get(f"{RETRIEVAL_SERVICE_URL}/retrieval/features/list")
        resp.raise_for_status()
        features = resp.json().get("features", [])
    logger.info(f"Retrieved {len(features)} features")
    return {"features": features}"""


async def retriever_health_tool():
    logger.info("Calling retrieval service health check")
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        resp = await client.get(f"{RETRIEVAL_SERVICE_URL}/retrieval/service/health")
        resp.raise_for_status()
        status = resp.json()
    logger.info("Retrieval service health check succeeded")
    return status



async def generator_tool(payload: dict):
    user_query = payload.get("user_query")
    context = payload.get("context", [])
    if not user_query:
        logger.warning("Missing 'user_query' in payload")
        return {"error": "Missing 'user_query'", "answer": ""}

    logger.info(f"Calling generation service with user_query={user_query!r} context_len={len(context)}")
    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            resp = await client.post(
                f"{GENERATION_SERVICE_URL}/generation/answer/generate",
                json={"user_query": user_query, "context": context[:TOP_K]},
            )
            resp.raise_for_status()
            gen_json = resp.json()
        logger.info(f"Generation service responded with keys: {list(gen_json.keys()) if isinstance(gen_json, dict) else 'non-dict'}")
        return gen_json if isinstance(gen_json, dict) else {"answer": str(gen_json)}
    except httpx.ReadTimeout:
        logger.error(f"Generator service timed out after {timeout_config.read}s for query={user_query}")
        return {"error": "Generator timeout", "answer": ""}
    except Exception as e:
        logger.exception(f"Generator error: {e}")
        return {"error": str(e), "answer": ""}


async def generator_health_tool():
    logger.info("Calling generation service health check")
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        resp = await client.get(f"{GENERATION_SERVICE_URL}/generation/service/health")
        resp.raise_for_status()
        status = resp.json()
    logger.info("Generation service health check succeeded")
    return status


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
    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            with open(kb_path, "rb") as f:
                files = {"file": (kb_path.name, f, "text/plain")}
                resp = await client.post(f"{INDEXING_SERVICE_URL}/indexing/index/add", files=files)
            resp.raise_for_status()
            result = resp.json()
        logger.info(f"Indexer response: {result}")
        return result
    except httpx.ReadTimeout:
        logger.error(f"Indexer tool timed out after {timeout_config.read}s")
        return {"error": "Indexer timeout"}
    except Exception as e:
        logger.exception(f"Indexer error: {e}")
        return {"error": str(e)}


"""async def indexer_fetch_and_index_tool():
    logger.info("Calling indexing service /index/fetch-and-index")
    try:
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            resp = await client.post(f"{INDEXING_SERVICE_URL}/indexing/index/fetch-and-index")
            resp.raise_for_status()
            result = resp.json()
        logger.info(f"/index/fetch-and-index response: {result}")
        return result
    except httpx.ReadTimeout:
        logger.error(f"Indexer fetch-and-index timed out after {timeout_config.read}s")
        return {"error": "Indexer fetch-and-index timeout"}
    except Exception as e:
        logger.exception(f"Indexer fetch-and-index error: {e}")
        return {"error": str(e)}"""


async def indexer_index_status_tool():
    logger.info("Calling indexing service /index/status")
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        resp = await client.get(f"{INDEXING_SERVICE_URL}/indexing/index/status")
        resp.raise_for_status()
        status = resp.json()
    logger.info("Index status retrieved successfully")
    return status


async def indexer_health_tool():
    logger.info("Calling indexing service health check")
    async with httpx.AsyncClient(timeout=timeout_config) as client:
        resp = await client.get(f"{INDEXING_SERVICE_URL}/indexing/service/health")
        resp.raise_for_status()
        status = resp.json()
    logger.info("Indexing service health check succeeded")
    return status
