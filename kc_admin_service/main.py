from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from error_responses import APIException, format_error
from routers import features as features_router, questions as questions_router
from db import Base, engine
import models
import asyncio
from db import SessionLocal
import crud
import traceback



app = FastAPI(title="Kitty Cash - AI Chat Admin API (Phase 1)" )



# @app.on_event("startup")
# async def periodic_feature_sync():
#     async def sync_loop():
#         while True:
#             db = SessionLocal()
#             try:
#                 result = crud.sync_features_from_retriever(db)
#                 print(f"[AutoSync] Success: {result}")
#             except Exception as e:
#                 print(f"[AutoSync] Failed: {e}")
#                 traceback.print_exc()  
#             finally:
#                 db.close()
#             await asyncio.sleep(60)  
#     asyncio.create_task(sync_loop())

@app.get("admin/health")
def health_check():
    return {"status": "kittycash admin is running"}

Base.metadata.create_all(bind=engine)

app.include_router(features_router.router)
app.include_router(questions_router.router)

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    body = {
        "success": False,
        "error": {
            "code": exc.code,
            "message": exc.message
        }
    }
    if exc.details:
        body["error"]["details"] = exc.details
    if exc.request_id:
        body["error"]["request_id"] = exc.request_id
    return JSONResponse(status_code=exc.status_code, content=body)

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):

    body = {
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected server error"
        }
    }
    return JSONResponse(status_code=500, content=body)
