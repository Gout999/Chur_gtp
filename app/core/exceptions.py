"""Global exception primitives."""
from fastapi import Request
from fastapi.responses import JSONResponse


class EduGuideError(Exception):
    """Domain-level exception for API services."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def eduguide_error_handler(_: Request, exc: EduGuideError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
