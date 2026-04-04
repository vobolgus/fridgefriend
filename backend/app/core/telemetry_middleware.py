# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false, reportMissingParameterType=false, reportImplicitOverride=false

from __future__ import annotations

import time
import uuid as uuid_mod
from typing import override

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
import structlog

from app.core.database import AsyncSessionLocal
from app.core.metrics import ACTIVE_REQUESTS_GAUGE, REQUEST_COUNTER, REQUEST_DURATION_HISTOGRAM
from app.models.api_request_log import ApiRequestLog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    wrapper_class=structlog.make_filtering_bound_logger(0),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def _get_handler_label(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path
    return request.url.path


def _get_status_group(status_code: int) -> str:
    return f"{status_code // 100}xx"


class TelemetryMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        structlog.contextvars.clear_contextvars()
        request_id = str(uuid_mod.uuid4())
        start = time.perf_counter()
        status_code = 500
        error_detail = None
        in_progress_handler = request.url.path
        handler_label = in_progress_handler

        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        ACTIVE_REQUESTS_GAUGE.labels(handler=in_progress_handler).inc()
        logger.info("request_started")

        try:
            response = await call_next(request)
            status_code = response.status_code
            handler_label = _get_handler_label(request)
            response.headers["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            error_detail = str(exc)[:500]
            handler_label = _get_handler_label(request)
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            duration_seconds = duration_ms / 1000
            status_group = _get_status_group(status_code)

            user_id = getattr(request.state, "user_id", None)
            persisted_user_id = uuid_mod.UUID(user_id) if isinstance(user_id, str) else None

            ACTIVE_REQUESTS_GAUGE.labels(handler=in_progress_handler).dec()
            REQUEST_DURATION_HISTOGRAM.labels(handler=handler_label, method=request.method).observe(duration_seconds)
            REQUEST_COUNTER.labels(
                handler=handler_label,
                method=request.method,
                status_group=status_group,
            ).inc()

            structlog.contextvars.bind_contextvars(
                user_id=user_id,
                handler=handler_label,
                status_code=status_code,
                status_group=status_group,
            )
            logger.info("request_completed", duration_ms=round(duration_ms, 2))

            try:
                async with AsyncSessionLocal() as session:
                    log_entry = ApiRequestLog(
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                        duration_ms=duration_ms,
                        user_id=persisted_user_id,
                        request_id=request_id,
                        error_detail=error_detail,
                    )
                    session.add(log_entry)
                    await session.commit()
            except Exception:
                logger.exception("request_persistence_failed")
            finally:
                structlog.contextvars.clear_contextvars()
