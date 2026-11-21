import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config.logging import request_id_ctx_var

logger = logging.getLogger("exam_scheduler")


class DomainException(Exception):
    """Base domain exception with typed error code and details."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: list[dict[str, Any]] | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


def format_error_response(
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "requestId": request_id or request_id_ctx_var.get(),
        }
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
        logger.warning(
            f"Domain error [{exc.code}]: {exc.message} on {request.method} {request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details: list[dict[str, Any]] = []
        for err in exc.errors():
            loc = " -> ".join(str(item) for item in err.get("loc", []))
            details.append(
                {
                    "field": loc,
                    "value": str(err.get("input", "")),
                    "issue": err.get("msg", "Invalid value"),
                }
            )

        logger.info(f"Validation error on {request.method} {request.url.path}: {details}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=format_error_response(
                code="VALIDATION_ERROR",
                message="Request payload failed validation.",
                details=details,
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        code_map = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            429: "RATE_LIMIT_EXCEEDED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = str(exc.detail) if isinstance(exc.detail, str) else "An HTTP error occurred."

        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(code=code, message=message),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = request_id_ctx_var.get()
        logger.exception(
            f"Unhandled exception on {request.method} {request.url.path} [ReqID: {req_id}]: {exc}"
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=format_error_response(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal server error occurred. Please contact support.",
                request_id=req_id,
            ),
        )
