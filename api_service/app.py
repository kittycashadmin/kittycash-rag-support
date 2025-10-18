# © 2025 Kittycash Team. All rights reserved to Trustnet Systems LLP.
import logging
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from mcp_client import KittyCashMCPClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api_server")

app = FastAPI(title="Kitty Cash API Server (MCP Client)", version="1.0.0")
mcp_client = KittyCashMCPClient()

@app.get("/health")
async def health_check():
    return {"status": "API Server with MCP running"}

#microservice name/feature/functionality

@app.post("/support/chat")
async def support_chat(request: Request):
    payload = await request.json()
    user_id = payload.get("user_id")
    message = payload.get("message")

    if not user_id or not message:
        raise HTTPException(status_code=400, detail="Missing 'user_id' or 'message'")

    logger.info(f"Received message from user {user_id}")

    try:
        routed = await mcp_client.route_and_call(message)
    except Exception as e:
        logger.exception(f"Error routing/calling tool: {e}")
        raise HTTPException(status_code=503, detail=f"Routing/Tool error: {e}")

    answer = routed.get("answer", "")
    logger.info(f"Returning answer preview: {answer[:240] if answer else '<empty>'}")

    return {"status": "success", "responses": [{"type": "text", "content": answer}]}

@app.post("/admin/index/upload")
async def admin_upload(file: UploadFile = File(...)):
    try:
        file_path = f"/data/kb_files/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())

        logger.info(f"Indexing file uploaded by admin: {file.filename}")
        result = await mcp_client.index(file_path)
        logger.info(f"Indexing result: {result}")
        return {"status": "success", "detail": result}
    except Exception as e:
        logger.exception(f"Indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    


@app.post("/kc_admin/similar-search")
async def kc_admin_similar_search(req: Request):
    payload = await req.json()
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing query")

    logger.info(f"[KC_ADMIN] Similar search requested: {query}")
    try:
        result = await mcp_client.call_tool("retriever_admin_search", {"query": query})
        return {"success": True, "data": result}
    except Exception as e:
        logger.exception(f"KC Admin similar search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

