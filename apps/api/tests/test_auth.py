"""
Authentication and Token Security Tests.
Tests Argon2, JWT, token rotation, and token family reuse revocation.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_registration_and_login_flow(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "email": "trader@oracle.institutional",
        "password": "StrongPassword99!#",
        "full_name": "Satoshi Nakamoto",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == reg_payload["email"].lower()
    assert user_data["role"] in ["admin", "user"]

    # 2. Login
    login_payload = {
        "email": "trader@oracle.institutional",
        "password": "StrongPassword99!#",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]

    # Verify refresh token cookie is set
    assert "btc_oracle_refresh" in login_resp.cookies
    refresh_token = login_resp.cookies["btc_oracle_refresh"]

    # 3. Access Protected /auth/me route
    headers = {"Authorization": f"Bearer {access_token}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "trader@oracle.institutional"

    # 4. Token Rotation: Refresh access token
    client.cookies.set("btc_oracle_refresh", refresh_token)
    ref_resp = await client.post("/api/v1/auth/refresh")
    assert ref_resp.status_code == 200
    new_token_data = ref_resp.json()
    assert "access_token" in new_token_data
    new_refresh = ref_resp.cookies.get("btc_oracle_refresh")
    assert new_refresh is not None
    assert new_refresh != refresh_token  # Rotated!

    # 5. Security Breach Test: Token Family Reuse Revocation
    # Presenting the old (already used) refresh token must trigger reuse detection and revocation
    client.cookies.set("btc_oracle_refresh", refresh_token)
    breach_resp = await client.post("/api/v1/auth/refresh")
    assert breach_resp.status_code == 401
    assert "reuse" in breach_resp.json()["detail"].lower()

    # Now presenting even the new refresh token should fail because the whole family was revoked
    client.cookies.set("btc_oracle_refresh", new_refresh)
    family_revoked_resp = await client.post("/api/v1/auth/refresh")
    assert family_revoked_resp.status_code == 401
