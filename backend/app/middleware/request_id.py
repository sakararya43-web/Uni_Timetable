import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.config.logging import request_id_ctx_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that inspects incoming requests for an X-Request-ID header.
    If absent, generates a fresh UUID-based identifier.
    Sets the ID into ContextVar for logging and echoes it in the response header.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        header_request_id = request.headers.get("X-Request-ID")
        request_id = header_request_id or f"req_{uuid.uuid4().hex[:16]}"

        token = request_id_ctx_var.set(request_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx_var.reset(token)
