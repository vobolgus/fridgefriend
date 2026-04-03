# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from .core.config import settings
from .core.database import engine
from .models import Base
from .modules.catalog.router import router as catalog_router
from .modules.inventory.router import router as inventory_router
from .modules.planning.router import router as planning_router
from .modules.recommendations.router import router as recommendations_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, debug=settings.DEBUG, lifespan=lifespan)
app.include_router(inventory_router)
app.include_router(catalog_router)
app.include_router(recommendations_router)
app.include_router(planning_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.VERSION}
