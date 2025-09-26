# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.

import argparse
import logging
import threading
from typing import Dict, List
from fastmcp import FastMCP
from fastapi import FastAPI
import uvicorn
from tools import retriever_tool, generator_tool, indexer_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("mcp_server")

mcp = FastMCP("KittyCash-MCP-Server")

# Tool metadata
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
        "name": "generator",
        "capabilities": ["generate", "answer"],
        "description": "Generates a user-facing answer given user query and retrieved context. Input: {user_query:str, context:list}. Uses internal LLM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_query": {"type": "string"},
                "context": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["user_query", "context"],
        },
        "examples": [
            "generator(user_query='Explain the settlement process', context=[{id:1, text:'...'}])"
        ],
    },
    {
        "name": "indexer",
        "capabilities": ["ingest", "index", "update_kb"],
        "description": "Uploads KB files and updates the FAISS index. Input: {kb_file: str path to local file}.",
        "input_schema": {
            "type": "object",
            "properties": {"kb_file": {"type": "string"}},
            "required": ["kb_file"],
        },
        "examples": ["indexer(kb_file='data/policies.txt')"],
    },
]

# Meta API for manifest discovery
app = FastAPI(title="KittyCash MCP Meta", version="1.0.0")

@app.get("/mcp/tools")
async def list_tools():
    return {"tools": TOOLS_MANIFEST}


def run_meta_api(host: str, port: int):
    uvicorn.run(app, host=host, port=port, log_level="info")


# MCP Tools
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
