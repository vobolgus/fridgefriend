# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]
    FastApiIntegration = None  # type: ignore[assignment]

from .core.config import settings
from .core.database import engine
from .models import Base
from .modules.analytics.router import router as analytics_router
from .modules.catalog.router import router as catalog_router
from .modules.households.router import router as households_router
from .modules.inventory.router import router as inventory_router
from .modules.notifications.router import router as notifications_router
from .modules.planning.router import router as planning_router
from .modules.recommendations.router import router as recommendations_router


if settings.SENTRY_DSN and sentry_sdk is not None and FastApiIntegration is not None:
    init_fn = getattr(sentry_sdk, "init", None)
    if callable(init_fn):
        _ = init_fn(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.0,
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, debug=settings.DEBUG, lifespan=lifespan)
app.include_router(inventory_router)
app.include_router(catalog_router)
app.include_router(households_router)
app.include_router(recommendations_router)
app.include_router(planning_router)
app.include_router(notifications_router)
app.include_router(analytics_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.VERSION}
