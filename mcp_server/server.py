import argparse
import logging
import threading
from typing import Dict, List
from fastmcp import FastMCP
from fastapi import FastAPI
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from tools import (
    retriever_tool,
    retriever_admin_search_tool,
    #retriever_features_tool,
    retriever_health_tool,
    generator_tool,
    generator_health_tool,
    indexer_tool,
    #indexer_fetch_and_index_tool,
    indexer_index_status_tool,
    indexer_health_tool,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mcp_server")

mcp = FastMCP("KittyCash-MCP-Server")

# Tool metadata with capabilities and input schemas
TOOLS_MANIFEST: List[Dict] = [
    {
        "name": "retriever",
        "capabilities": ["search", "semantic_search"],
        "description": "Semantic vector search over knowledge base. Input: {query: str}. Returns top-k documents with score and snippet.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "examples": ["retriever(query='how to settle a contribution')"],
    },
    {
        "name": "retriever_admin_search",
        "capabilities": ["search", "admin_search"],
        "description": "Admin-level feature-scoped search. Input: {query: str}. Returns documents plus all feature questions.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        "examples": ["retriever_admin_search(query='payment refund issue')"],
    },
    # {
    #     "name": "retriever_features",
    #     "capabilities": ["list_features"],
    #     "description": "Lists all defined features for domain-aware clients.",
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {},
    #         "required": [],
    #     },
    #     "examples": ["retriever_features()"],
    # },

    {
        "name": "generator",
        "capabilities": ["generate", "answer"],
        "description": "Generates user-facing answer from user query and context using LLM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_query": {"type": "string"},
                "context": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["user_query", "context"],
        },
        "examples": [
            "generator(user_query='Explain settlement process', context=[{id:1, text:'...'}])"
        ],
    },

    {
        "name": "indexer",
        "capabilities": ["ingest", "index", "update_kb"],
        "description": "Uploads KB files and updates the FAISS index. Input: {kb_file: string path}.",
        "input_schema": {
            "type": "object",
            "properties": {"kb_file": {"type": "string"}},
            "required": ["kb_file"],
        },
        "examples": ["indexer(kb_file='data/policies.txt')"],
    },
    # {
    #     "name": "indexer_fetch_and_index",
    #     "capabilities": ["fetch_and_index"],
    #     "description": "Fetch unindexed questions and index them in batch.",
    #     "input_schema": {
    #         "type": "object",
    #         "properties": {},
    #         "required": [],
    #     },
    #     "examples": ["indexer_fetch_and_index()"],
    # },
    {
        "name": "indexer_index_status",
        "capabilities": ["index_status"],
        "description": "Returns current FAISS index metadata and stats.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
        "examples": ["indexer_index_status()"],
    },

]

# Meta API for manifest discovery
app = FastAPI(title="KittyCash MCP Meta", version="1.0.0")


@app.get("/mcp/tools")
async def list_tools():
    return {"tools": TOOLS_MANIFEST}

@app.get("/mcpserver/service/health")
def health_check():
    return {"status": "MCPServer is running"}


# MCP Tool Registrations

@mcp.tool(name="retriever")
async def retriever(query: str):
    logger.info(f"Tool 'retriever' called with query: {query!r}")
    try:
        result = await retriever_tool({"query": query})
        logger.info(f"'retriever' returning {len(result.get('results', []))} results")
        return result
    except Exception as e:
        logger.exception(f"Retriever error: {e}")
        return {"error": str(e), "results": []}


@mcp.tool(name="retriever_admin_search")
async def retriever_admin_search(query: str):
    logger.info(f"Tool 'retriever_admin_search' called with query: {query!r}")
    try:
        result = await retriever_admin_search_tool({"query": query})
        logger.info(f"'retriever_admin_search' returning results")
        return result
    except Exception as e:
        logger.exception(f"Retriever admin search error: {e}")
        return {"error": str(e)}


"""@mcp.tool(name="retriever_features")
async def retriever_features():
    logger.info("Tool 'retriever_features' called")
    try:
        result = await retriever_features_tool()
        logger.info(f"'retriever_features' returning {len(result.get('features', []))} features")
        return result
    except Exception as e:
        logger.exception(f"Retriever features error: {e}")
        return {"error": str(e), "features": []}"""





@mcp.tool(name="generator")
async def generator(user_query: str, context: list):
    logger.info(f"Tool 'generator' called with user_query={user_query!r} context_len={len(context) if context else 0}")
    try:
        result = await generator_tool({"user_query": user_query, "context": context})
        logger.info(f"'generator' returned answer preview: {(result.get('answer') or '')[:240]}")
        return result
    except Exception as e:
        logger.exception(f"Generator error: {e}")
        return {"error": str(e), "answer": ""}





@mcp.tool(name="indexer")
async def indexer(kb_file: str):
    logger.info(f"Tool 'indexer' called with kb_file={kb_file!r}")
    try:
        result = await indexer_tool({"kb_file": kb_file})
        logger.info(f"'indexer' response: {result}")
        return result
    except Exception as e:
        logger.exception(f"Indexer error: {e}")
        return {"error": str(e)}


"""@mcp.tool(name="indexer_fetch_and_index")
async def indexer_fetch_and_index():
    logger.info("Tool 'indexer_fetch_and_index' called")
    try:
        result = await indexer_fetch_and_index_tool()
        logger.info(f"'indexer_fetch_and_index' response: {result}")
        return result
    except Exception as e:
        logger.exception(f"Indexer fetch-and-index error: {e}")
        return {"error": str(e)}"""


@mcp.tool(name="indexer_index_status")
async def indexer_index_status():
    logger.info("Tool 'indexer_index_status' called")
    try:
        result = await indexer_index_status_tool()
        logger.info(f"'indexer_index_status' returned status")
        return result
    except Exception as e:
        logger.exception(f"Indexer index status error: {e}")
        return {"error": str(e)}





@mcp.tool(name="health")
async def health():
    logger.info("Running healthcheck on all tools")
    try:
        retr = await retriever_health_tool()
        gen = await generator_health_tool()
        ind = await indexer_health_tool()
        return {
            "retriever": retr,
            "generator": gen,
            "indexer": ind
        }
    except Exception as e:
        logger.exception(f"Health check error: {e}")
        return {"error": str(e)}


def run_meta_api(host: str, port: int):
    uvicorn.run(app, host=host, port=port, log_level="info")


# Entrypoint
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=9000, help="Port for FastMCP transport")
    parser.add_argument("--meta-port", type=int, default=9001, help="Port for manifest HTTP endpoint (/mcp/tools)")
    parser.add_argument("--transport", default="http", choices=["http", "stdio"])
    args = parser.parse_args()

    t = threading.Thread(target=run_meta_api, args=(args.host, args.meta_port), daemon=True)
    t.start()
    logger.info(f"Started MCP manifest API at http://{args.host}:{args.meta_port}/mcp/tools")

    logger.info(
        "Starting FastMCP server '%s' on %s:%s (transport=%s)",
        mcp.name, args.host, args.port, args.transport
    )
    mcp.run(host=args.host, port=args.port, transport=args.transport)
