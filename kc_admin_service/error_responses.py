from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Optional, Any, Dict

class APIException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.request_id = request_id

def format_error(code: str, message: str, details: Optional[Dict] = None, request_id: Optional[str] = None):
    err = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    if details is not None:
        err["error"]["details"] = details
    if request_id:
        err["error"]["request_id"] = request_id
    return err

def raise_api_error(code: str, message: str, status_code: int = 400, details: Optional[Dict] = None, request_id: Optional[str] = None):
    raise APIException(code=code, message=message, status_code=status_code, details=details, request_id=request_id)
