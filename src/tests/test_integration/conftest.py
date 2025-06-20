# src/tests/test_integration/conftest.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
import os

# Жорстко забиваємо DSN з вашого docker-compose
POSTGRES_DSN = "postgresql+asyncpg://admin:some_password@localhost:5432/movies_db"
API_BASE    = "http://localhost:8000"

@pytest.fixture(scope="session")
async def db_conn():
    engine = create_async_engine(POSTGRES_DSN, future=True)
    async with engine.begin() as conn:
        yield conn
    await engine.dispose()

@pytest.fixture
async def client():
    cli = AsyncClient(base_url=API_BASE, timeout=30.0)
    yield cli
    await cli.aclose()
