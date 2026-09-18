from fastapi import FastAPI

from app.api import health
from app.core.exceptions.base import AppException
from app.core.exceptions.handlers import RequestValidationError, validation_exception_handler, app_exception_handler, global_exception_handler

app = FastAPI()

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(health.router)
