from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
import logging

from app.core.exceptions.base import AppException

logger = logging.getLogger(__name__)

async def app_exception_handler(request: Request, exc: AppException):

    error_content = exc.to_dict()
    error_content['timestamp'] = datetime.now(timezone.utc).isoformat()

    logger.error(
        f"Error: {exc.detail} | "
        f"Status: {exc.status_code} | "
        f"Code: {exc.error_code} | "
        f"Path: {request.url.path}"
    )

    return JSONResponse(status_code=exc.status_code,
                        content=error_content)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    for error in exc.errors():
        loc = ".".join(str(item) for item in error["loc"])
        formatted_errors.append({
            "field": loc,
            "message": error["msg"],
            "error_type": error["type"]
        })
    
    error_content = {
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "detail": formatted_errors,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_content)


async def global_exception_handler(request: Request, exc: Exception):
    error_content = {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "detail": "Internal server error",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.error(f"Unhandled exception: {exc}", exc_info=True)  

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                        content=error_content)