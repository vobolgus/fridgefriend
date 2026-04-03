from fastapi import FastAPI

from app.core.config import settings


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, debug=settings.DEBUG)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.VERSION}
