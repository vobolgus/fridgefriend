from collections.abc import AsyncIterator, Generator

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.core.database as database_module
from app.core.config import settings
from app.main import app as fastapi_app
from app.models import Base


@pytest.fixture
def app() -> FastAPI:
    return fastapi_app


@pytest_asyncio.fixture
async def _test_engine():
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    original_engine = database_module.engine
    original_session_local = database_module.AsyncSessionLocal
    database_module.engine = test_engine
    database_module.AsyncSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)

    yield test_engine

    database_module.engine = original_engine
    database_module.AsyncSessionLocal = original_session_local
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(_test_engine) -> AsyncIterator[AsyncSession]:
    async with database_module.AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(app: FastAPI, _test_engine) -> AsyncIterator[httpx.AsyncClient]:
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
