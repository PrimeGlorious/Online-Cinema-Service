import uuid
import anyio
import psycopg2
import pytest
from httpx import AsyncClient

API_BASE  = "http://localhost:8000"
PROF_BASE = "/api/v1/profiles/"
DSN       = "dbname=movies_db user=admin password=some_password host=localhost port=5432"


def _get_token_from_db(email: str, table: str) -> str:
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


async def create_user_and_token():
    # Реєструємо та активуємо звичайного користувача
    email = f"user_{uuid.uuid4().hex}@example.com"
    pw = "Qwerty123!"

    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(
            "/api/v1/accounts/register/",
            json={"email": email, "password": pw, "password_confirm": pw},
        )
    assert r.status_code == 201, f"Registration failed: {r.text}"

    token = await anyio.to_thread.run_sync(_get_token_from_db, email, "activation_tokens")
    assert token, "Activation token missing"

    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(f"/api/v1/accounts/activate/{token}/")
    assert r.status_code == 200, f"Activation failed: {r.text}"

    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(
            "/api/v1/accounts/login/",
            json={"email": email, "password": pw},
        )
    assert r.status_code == 200, f"Login failed: {r.text}"
    return {"email": email, "access_token": r.json()["access_token"]}


@pytest.mark.asyncio
async def test_user_profile_crud_lifecycle():
    user = await create_user_and_token()
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    # CREATE
    data = {"first_name": "Test", "last_name": "User", "gender": "man", "info": "Hello"}
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(PROF_BASE, json=data, headers=headers)
    assert r.status_code in (200, 201), f"Create failed: {r.text}"
    prof = r.json()
    assert prof["first_name"] == "Test"

    # GET /me
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(PROF_BASE + "me", headers=headers)
    assert r.status_code == 200, f"Get own failed: {r.text}"
    assert r.json()["id"] == prof["id"]

    # PATCH /me
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.patch(PROF_BASE + "me", json={"info": "Updated"}, headers=headers)
    assert r.status_code == 200, f"Update own failed: {r.text}"
    assert r.json()["info"] == "Updated"

    # Unauthorized cannot fetch someone else's
    other = await create_user_and_token()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(PROF_BASE + str(prof["id"]), headers=other_headers)
    assert r.status_code == 403, f"Should forbid access for other user, got {r.status_code}"

    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(PROF_BASE + str(prof["id"]))
    assert r.status_code == 401, f"Should be Unauthorized without token, got {r.status_code}"


@pytest.mark.usefixtures("admin_credentials")
@pytest.mark.asyncio
async def test_admin_profile_crud(admin_credentials):
    admin_headers = {"Authorization": f"Bearer {admin_credentials['access_token']}"}

    # LIST
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(PROF_BASE, headers=admin_headers)
    assert r.status_code == 200, f"List failed: {r.text}"
    assert isinstance(r.json(), list)

    # Створимо профіль іншого користувача
    other = await create_user_and_token()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(PROF_BASE, json={"first_name": "X", "last_name": "Y"}, headers=other_headers)
    assert r.status_code in (200, 201), f"Other create failed: {r.text}"
    prof = r.json()

    # Admin видаляє цей профіль
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.delete(PROF_BASE + str(prof["id"]), headers=admin_headers)
    assert r.status_code in (200, 204), f"Delete failed: {r.text}"
