# pyright: reportMissingImports=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from fastapi import FastAPI

from .core.config import settings
from .modules.catalog.router import router as catalog_router
from .modules.inventory.router import router as inventory_router
from .modules.recommendations.router import router as recommendations_router


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, debug=settings.DEBUG)
app.include_router(inventory_router)
app.include_router(catalog_router)
app.include_router(recommendations_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.VERSION}
