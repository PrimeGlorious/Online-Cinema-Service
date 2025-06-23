import uuid
import re
import pytest
import anyio
import psycopg2
import httpx

API_BASE = "http://localhost:8000"
DSN = "dbname=movies_db user=admin password=some_password host=localhost port=5432"

REGISTER   = "/api/v1/accounts/register/"
ACTIVATE   = "/api/v1/accounts/activate/"
LOGIN      = "/api/v1/accounts/login/"
REFRESH    = "/api/v1/accounts/token/refresh/"
LOGOUT     = "/api/v1/accounts/logout/"
CHANGE_PW  = "/api/v1/accounts/change-password/"
RESET_REQ  = "/api/v1/accounts/reset-password-request/"
RESET      = "/api/v1/accounts/reset-password/"

def _get_token_from_db(email: str, table: str) -> str:
    """Sync helper to pull a single token from the given table."""
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()
    cur.execute(
        f"SELECT token FROM {table} "
        "WHERE user_id = (SELECT id FROM users WHERE email = %s)",
        (email,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0]

@pytest.mark.asyncio
async def test_full_user_account_flow():
    # 1) Register
    email = f"user_{uuid.uuid4().hex}@example.com"
    pw    = "Password123!"
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(REGISTER, json={
            "email": email, "password": pw, "password_confirm": pw
        })
        assert r.status_code == 201, r.text

    # 2) Pull activation token from DB
    activation_token = await anyio.to_thread.run_sync(
        _get_token_from_db, email, "activation_tokens"
    )
    assert activation_token, "Activation token missing in DB"

    # 3) Activate
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.get(f"{ACTIVATE}{activation_token}/")
        assert r.status_code == 200, r.text
        assert "activated" in r.json().get("message", "").lower()

    # 4) Login
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(LOGIN, json={"email": email, "password": pw})
        assert r.status_code == 200, r.text
        tokens = r.json()
        at = tokens["access_token"]
        rt = tokens["refresh_token"]

    # 5) Refresh
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(REFRESH, json={"refresh_token": rt})
        assert r.status_code == 200, r.text
        new = r.json()
        assert new["access_token"] != at
        at, rt = new["access_token"], new["refresh_token"]

    # 6) Logout
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(LOGOUT, json={"refresh_token": rt})
        assert r.status_code == 204

    # 7) Change password
    new_pw = "Newpass123!"
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(
            CHANGE_PW,
            headers={"Authorization": f"Bearer {at}"},
            json={
                "old_password": pw,
                "new_password": new_pw,
                "new_password_repeat": new_pw,
            },
        )
        assert r.status_code in (200, 204), r.text

    # 8) Request password reset
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(RESET_REQ, json={"email": email})
        assert r.status_code in (200, 204), r.text

    # 9) Pull reset token from DB
    reset_token = await anyio.to_thread.run_sync(
        _get_token_from_db, email, "password_reset_tokens"
    )
    assert reset_token, "Reset token missing in DB"

    # 10) Confirm reset
    final_pw = "Finalpass123!"
    async with httpx.AsyncClient(base_url=API_BASE, timeout=30.0) as api:
        r = await api.post(RESET, json={
            "token": reset_token,
            "new_password": final_pw,
            "new_password_repeat": final_pw,
        })
        assert r.status_code in (200, 204), r.text
