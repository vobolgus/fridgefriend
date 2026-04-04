# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownMemberType=false

from __future__ import annotations

from typing import Final

from fastapi import FastAPI
from prometheus_client import Counter, Gauge, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info

SLO_BUCKETS: Final[tuple[float, ...]] = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 8.0, 10.0)
METRIC_NAMESPACE: Final[str] = "fridgefriend"

REQUEST_DURATION_HISTOGRAM = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    labelnames=("handler", "method"),
    buckets=SLO_BUCKETS,
    namespace=METRIC_NAMESPACE,
)

REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    labelnames=("handler", "method", "status_group"),
    namespace=METRIC_NAMESPACE,
)

ACTIVE_REQUESTS_GAUGE = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress.",
    labelnames=("handler",),
    namespace=METRIC_NAMESPACE,
)

def _noop_instrumentation(_: Info) -> None:
    return None


def setup_metrics(app: FastAPI) -> None:
    instrumentator = Instrumentator()
    instrumentator.add(_noop_instrumentation)
    instrumentator.instrument(
        app,
        metric_namespace=METRIC_NAMESPACE,
        latency_lowr_buckets=SLO_BUCKETS,
    )
    instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
