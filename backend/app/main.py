# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownMemberType=false

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator, Awaitable
import asyncio
import inspect
import os
import time
from typing import AsyncContextManager, Protocol, cast, runtime_checkable

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]
    FastApiIntegration = None  # type: ignore[assignment]

from .core.config import settings
from .core.database import engine
from .core.metrics import setup_metrics
from .core.redis import get_redis
from .models import Base
from .modules.analytics.router import router as analytics_router
from .modules.catalog.router import router as catalog_router
from .modules.households.router import router as households_router
from .modules.inventory.router import router as inventory_router
from .modules.notifications.router import router as notifications_router
from .modules.planning.router import router as planning_router
from .modules.recommendations.router import router as recommendations_router

_ = os.environ.setdefault("TZ", "UTC")
if hasattr(time, "tzset"):
    time.tzset()


@runtime_checkable
class RedisHealthClient(Protocol):
    def ping(self) -> Awaitable[bool] | bool:
        ...

    def aclose(self) -> Awaitable[None] | None:
        ...


@runtime_checkable
class ConnectionHealthClient(Protocol):
    def execute(self, statement: object) -> Awaitable[object] | object:
        ...


@runtime_checkable
class EngineHealthClient(Protocol):
    def connect(self) -> AsyncContextManager[ConnectionHealthClient]:
        ...


async def _await_if_needed(value: Awaitable[object] | object) -> object:
    if inspect.isawaitable(value):
        return await cast(Awaitable[object], value)
    return value


if settings.SENTRY_DSN and sentry_sdk is not None and FastApiIntegration is not None:
    init_fn = getattr(sentry_sdk, "init", None)
    if callable(init_fn):
        _ = init_fn(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            environment=settings.SENTRY_ENVIRONMENT,
        )


async def _seed_fixture_recipes() -> None:
    from uuid import UUID

    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from .models.recipe import Recipe
    from .modules.recommendations.fixture_recipes import FIXTURE_RECIPES

    async with AsyncSession(engine) as session:
        count = (await session.execute(select(func.count()).select_from(Recipe))).scalar() or 0
        if count > 0:
            return

        for data in FIXTURE_RECIPES:
            recipe = Recipe(
                id=UUID(str(data["id"])),
                title=str(data["title"]),
                prep_minutes=int(data.get("prep_minutes", 0)),
                image_url=str(data.get("image_url", "")) or None,
                source_url=str(data.get("source_url", "")) or None,
                summary=str(data.get("summary", "")) or None,
                instructions=data.get("instructions"),
                cuisines=data.get("cuisines"),
                servings=int(data.get("servings", 2)),
                nutrition=data.get("nutrition"),
                dietary_tags=data.get("dietary_tags", []),
                ingredients=data.get("ingredients", []),
            )
            session.add(recipe)
        await session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.ENVIRONMENT == "production" and "sqlite" in settings.DATABASE_URL:
        raise RuntimeError("Production must use PostgreSQL, not SQLite")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_fixture_recipes()
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, debug=settings.DEBUG, lifespan=lifespan)

from .core.telemetry_middleware import TelemetryMiddleware
app.add_middleware(TelemetryMiddleware)

app.include_router(inventory_router)
app.include_router(catalog_router)
app.include_router(households_router)
app.include_router(recommendations_router)
app.include_router(planning_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
setup_metrics(app)


def get_engine() -> EngineHealthClient:
    return cast(EngineHealthClient, cast(object, engine))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.VERSION}


@app.get("/health/ready")
async def readiness() -> JSONResponse:
    database_check: dict[str, str] = {"status": "healthy"}
    redis_check: dict[str, str] = {"status": "healthy"}

    try:
        async with asyncio.timeout(2):
            async with get_engine().connect() as conn:
                _ = await _await_if_needed(conn.execute(text("SELECT 1")))
    except Exception as exc:
        database_check = {"status": "unhealthy", "detail": str(exc)}

    redis_client_raw = await get_redis()
    redis_client = redis_client_raw if isinstance(redis_client_raw, RedisHealthClient) else None
    if redis_client is None:
        redis_check = {"status": "unhealthy", "detail": "Redis client unavailable"}
    else:
        try:
            async with asyncio.timeout(2):
                _ = await _await_if_needed(redis_client.ping())
        except Exception as exc:
            redis_check = {"status": "unhealthy", "detail": str(exc)}
        finally:
            close_method = getattr(redis_client, "aclose", None)
            if callable(close_method):
                _ = await _await_if_needed(close_method())

    checks = {"database": database_check, "redis": redis_check}
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    payload = {"status": "ready" if all_healthy else "unhealthy", "checks": checks}

    return JSONResponse(
        status_code=status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload,
    )
