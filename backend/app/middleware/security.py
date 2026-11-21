"""Security, Rate Limiting, and Idempotency Middleware.

PRD §19, Tasks P14.2, P14.3, P14.16.
"""

import threading
import time
from collections import defaultdict
from collections.abc import Callable
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces enterprise HTTP security headers across all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # OWASP Recommended Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self' data:; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'; "
            "base-uri 'self';"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window in-memory rate limiter per IP address.
    Protects login, imports, and heavy schedule generation endpoints.
    """

    def __init__(self, app: object, default_limit: int = 200, window_seconds: int = 60) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

        # Sensitive endpoint route thresholds
        self.route_limits: dict[str, int] = {
            "/api/v1/auth/login": 10,
            "/api/v1/imports": 20,
            "/generate": 15,
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if rate-limit bypass header is set (for internal tests)
        if request.headers.get("X-Bypass-Rate-Limit") == "1":
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        path = request.url.path

        # Determine threshold for this path
        limit = self.default_limit
        for route_prefix, route_limit in self.route_limits.items():
            if route_prefix in path:
                limit = route_limit
                break

        key = f"{client_ip}:{path}"
        now = time.time()

        with self._lock:
            # Purge timestamps outside sliding window
            cutoff = now - self.window_seconds
            self._history[key] = [t for t in self._history[key] if t > cutoff]

            if len(self._history[key]) >= limit:
                request_id = request.headers.get("X-Request-ID", "unknown")
                return JSONResponse(
                    status_code=429,
                    content={
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit of {limit} requests per {self.window_seconds}s exceeded for {path}. Please try again later.",
                        "requestId": request_id,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                    headers={"Retry-After": str(self.window_seconds)},
                )

            self._history[key].append(now)

        return await call_next(request)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency guard against double-clicks and repeated submissions.
    Inspects Idempotency-Key on mutating POST/PATCH requests.
    """

    def __init__(self, app: object, ttl_seconds: int = 60) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, int, bytes, dict[str, str]]] = {}
        self._active_keys: set[str] = set()
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in ("POST", "PATCH"):
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        now = time.time()

        with self._lock:
            # Clean expired keys
            expired = [k for k, (exp, _, _, _) in self._cache.items() if exp < now]
            for k in expired:
                del self._cache[k]

            # Check if key is currently executing (concurrent double submission)
            if idempotency_key in self._active_keys:
                return JSONResponse(
                    status_code=409,
                    content={
                        "code": "CONCURRENT_REQUEST_IN_PROGRESS",
                        "message": "A request with this Idempotency-Key is currently being processed.",
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                )

            # Return cached response if present
            if idempotency_key in self._cache:
                _, status_code, body, headers = self._cache[idempotency_key]
                return Response(content=body, status_code=status_code, headers=headers)

            self._active_keys.add(idempotency_key)

        try:
            response: Response = await call_next(request)

            # Consume response body to cache it
            response_body = b""
            async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                response_body += chunk if isinstance(chunk, bytes) else chunk.encode()

            headers = dict(response.headers)
            headers["X-Idempotent-Replay"] = "false"

            with self._lock:
                self._cache[idempotency_key] = (
                    now + self.ttl_seconds,
                    response.status_code,
                    response_body,
                    headers,
                )

            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=headers,
                media_type=response.media_type,
            )
        finally:
            with self._lock:
                self._active_keys.discard(idempotency_key)
