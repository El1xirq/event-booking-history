from app.core.exceptions.base import AppException


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail=detail, status_code=404, error_code="NOT_FOUND")


class PermissionDeniedException(AppException):
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=403, error_code="FORBIDDEN")


class ConflictException(AppException):
    def __init__(self, detail):
        super().__init__(detail=detail, status_code=409, error_code="CONFLICT")


class InvalidTokenException(AppException):
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail=detail, status_code=401, error_code="UNAUTHORIZED")


class DatabaseException(AppException):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(detail=detail, status_code=500, error_code="DATABASE_ERROR")


class InvalidRequestException(AppException):
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(detail=detail, status_code=422, error_code="UNPROCESSABLE_CONTENT")


class InvalidCredentialsException(AppException):
    def __init__(self, detail: str = "Invalid user credentials"):
        super().__init__(detail=detail, status_code=401, error_code="UNAUTHORIZED")


        