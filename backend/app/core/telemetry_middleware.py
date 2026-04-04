"""HTTP request telemetry middleware for API observability."""

from __future__ import annotations

import time
import uuid as uuid_mod

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.database import AsyncSessionLocal
from app.models.api_request_log import ApiRequestLog


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request to api_request_log for dashboard consumption."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid_mod.uuid4())
        start = time.perf_counter()
        status_code = 500
        error_detail = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            error_detail = str(exc)[:500]
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000

            # Extract user_id from request state if auth middleware set it
            user_id = getattr(request.state, "user_id", None)

            # Fire-and-forget: write log row without blocking response
            try:
                async with AsyncSessionLocal() as session:
                    log_entry = ApiRequestLog(
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        user_id=user_id,
                        request_id=request_id,
                        error_detail=error_detail,
                    )
                    session.add(log_entry)
                    await session.commit()
            except Exception:
                pass  # Telemetry failure must never break the API
