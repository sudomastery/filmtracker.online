"""
Tests for authentication endpoints:
  POST /auth/register
  POST /auth/login
  POST /auth/refresh
  POST /auth/logout
  GET  /users/me
"""
import pytest
from httpx import AsyncClient


# ─── Helpers ───────────────────────────────────────────────────────────────

async def register(client: AsyncClient, username: str, suffix: str = "") -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "username": f"{username}{suffix}",
        "email": f"{username}{suffix}@test.com",
        "password": "password123",
    })
    return resp


# ─── Register ──────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    resp = await register(client, "newuser")
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_register_duplicate_username(client: AsyncClient):
    await register(client, "dupuser")
    resp = await register(client, "dupuser")
    assert resp.status_code == 400
    assert "username" in resp.json()["detail"]


async def test_register_duplicate_email(client: AsyncClient):
    # First user
    await client.post("/api/v1/auth/register", json={
        "username": "user1dup",
        "email": "dupe@test.com",
        "password": "password123",
    })
    # Second user, same email
    resp = await client.post("/api/v1/auth/register", json={
        "username": "user2dup",
        "email": "dupe@test.com",
        "password": "password123",
    })
    assert resp.status_code == 400
    assert "email" in resp.json()["detail"]


async def test_register_sets_username_lowercase(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "CamelUser",
        "email": "camel@test.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    # Verify username stored as-is (routes lower it when checking)
    tokens = resp.json()
    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_resp.status_code == 200


# ─── Login ─────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient):
    await register(client, "loginok")
    resp = await client.post("/api/v1/auth/login", json={
        "username": "loginok",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client: AsyncClient):
    await register(client, "wrongpw")
    resp = await client.post("/api/v1/auth/login", json={
        "username": "wrongpw",
        "password": "notthepassword",
    })
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "nobody",
        "password": "password123",
    })
    assert resp.status_code == 401


async def test_login_by_email(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "emaillogin",
        "email": "emaillogin@test.com",
        "password": "password123",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "emaillogin@test.com",
        "password": "password123",
    })
    assert resp.status_code == 200


# ─── Refresh ───────────────────────────────────────────────────────────────

async def test_refresh_token(client: AsyncClient):
    reg = (await register(client, "refreshme")).json()
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": reg["refresh_token"]
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_with_invalid_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": "this.is.not.a.real.token"
    })
    assert resp.status_code == 401


# ─── Logout ────────────────────────────────────────────────────────────────

async def test_logout_success(client: AsyncClient):
    reg = (await register(client, "logoutme")).json()
    refresh = reg["refresh_token"]

    resp = await client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert resp.status_code == 204

    # Refresh should now fail (token revoked)
    resp2 = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp2.status_code == 401


# ─── /users/me ─────────────────────────────────────────────────────────────

async def test_get_me(client: AsyncClient):
    reg = (await register(client, "meuser")).json()
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {reg['access_token']}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "meuser"
    assert "follower_count" in data
    assert "following_count" in data


async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_get_me_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
