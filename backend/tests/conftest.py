from collections.abc import AsyncIterator, Generator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.main import app as fastapi_app
from app.models import Base


@pytest.fixture
def app() -> FastAPI:
    return fastapi_app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        ) as async_client:
            yield async_client


@pytest.fixture
def test_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def enable_mock_auth_by_default() -> Generator[None, None, None]:
    previous = settings.AUTH_MOCK
    settings.AUTH_MOCK = True
    try:
        yield
    finally:
        settings.AUTH_MOCK = previous


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal(bind=engine) as session:
        yield session

    await engine.dispose()
