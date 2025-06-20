import uuid
import re
import anyio
import psycopg2
import pytest
from httpx import AsyncClient

PROF_BASE = "/api/v1/profiles/"
API_BASE  = "http://localhost:8000"
DSN       = "dbname=movies_db user=admin password=some_password host=localhost port=5432"


def _get_token_from_db(email: str, table: str) -> str:
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        f"SELECT token FROM {table} "
        "WHERE user_id = (SELECT id FROM users WHERE email = %s)",
        (email,),
    )
    row = cur.fetchone() or [None]
    cur.close()
    conn.close()
    return row[0]


async def create_user_and_token():
    email = f"user_{uuid.uuid4().hex}@example.com"
    pw    = "Qwerty123!"

    # 1) Реєстрація
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        await api.post(
            "/api/v1/accounts/register/",
            json={"email": email, "password": pw, "password_confirm": pw},
        )

    # 2) Дістаємо activation_token із БД
    activation_token = await anyio.to_thread.run_sync(
        _get_token_from_db, email, "activation_tokens"
    )

    # 3) Активація
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        await api.get(f"/api/v1/accounts/activate/{activation_token}/")

    # 4) Логін, повертаємо токен
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        resp = await api.post(
            "/api/v1/accounts/login/",
            json={"email": email, "password": pw},
        )
    data = resp.json()
    return {"email": email, "password": pw, "access_token": data["access_token"]}


@pytest.mark.asyncio
async def test_profile_crud_as_user():
    user = await create_user_and_token()
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    # CREATE
    data = {"first_name": "Test", "last_name": "User", "gender": "man", "info": "Hello"}
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(PROF_BASE, json=data, headers=headers)
    assert r.status_code == 200
    prof = r.json()
    assert prof["first_name"] == "Test"

    # GET /me
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r2 = await api.get(PROF_BASE + "me", headers=headers)
    assert r2.status_code == 200

    # PATCH /me
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r3 = await api.patch(
            PROF_BASE + "me", json={"info": "Updated"}, headers=headers
        )
    assert r3.json()["info"] == "Updated"

    # Ensure cannot access another’s profile
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r4 = await api.get(PROF_BASE + f"{prof['id']}", headers={"Authorization": "Bearer wrong"})
    assert r4.status_code == 403


@pytest.mark.usefixtures("admin_credentials")
@pytest.mark.asyncio
async def test_profile_crud_as_admin(admin_credentials):
    headers = {"Authorization": f"Bearer {admin_credentials['access_token']}"}

    # 1) Admin бачить всі профілі
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(PROF_BASE, headers=headers)
    assert r.status_code == 200
    profiles = r.json()
    assert isinstance(profiles, list)

    # 2) Створюємо профіль іншого користувача
    other = await create_user_and_token()
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(PROF_BASE, json={"first_name": "X", "last_name": "Y"}, headers={"Authorization": f"Bearer {other['access_token']}"})
    prof = r.json()

    # 3) Admin видаляє чужий профіль
    async with AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r_del = await api.delete(PROF_BASE + f"{prof['id']}", headers=headers)
    assert r_del.status_code == 200 or r_del.status_code == 204
