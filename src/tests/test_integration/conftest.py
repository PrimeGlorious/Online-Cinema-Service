import pytest
import uuid
import anyio
import psycopg2
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
import os

# DSN for sync connections (used to fetch tokens and update roles)
DSN = "dbname=movies_db user=admin password=some_password host=localhost port=5432"
# Async DSN for SQLAlchemy
POSTGRES_DSN = "postgresql+asyncpg://admin:some_password@localhost:5432/movies_db"
API_BASE = "http://localhost:8000"

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

def _get_token_from_db_sync(email: str, table: str) -> str:
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        f"SELECT token FROM {table} "
        "WHERE user_id = (SELECT id FROM users WHERE email = %s)",
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

def _make_admin_sync(email: str):
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 'admin' WHERE email = %s", (email,))
    conn.commit()
    cur.close()
    conn.close()

@pytest.fixture
async def admin_credentials():
    email = f"admin_{uuid.uuid4().hex}@example.com"
    pw = "Adminpass123!"

    # Register admin user
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(
            "/api/v1/accounts/register/",
            json={"email": email, "password": pw, "password_confirm": pw},
        )
    assert r.status_code == 201, f"Admin registration failed: {r.text}"

    # Get activation token
    activation_token = await anyio.to_thread.run_sync(
        _get_token_from_db_sync, email, "activation_tokens"
    )
    assert activation_token, "Admin activation token missing in DB"

    # Activate admin user
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(f"/api/v1/accounts/activate/{activation_token}/")
    assert r.status_code == 200, f"Admin activation failed: {r.text}"

    # Promote to admin role
    await anyio.to_thread.run_sync(_make_admin_sync, email)

    # Login as admin
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(
            "/api/v1/accounts/login/", json={"email": email, "password": pw}
        )
    assert r.status_code == 200, f"Admin login failed: {r.text}"
    tokens = r.json()

    return {"email": email, "password": pw, "access_token": tokens["access_token"]}
