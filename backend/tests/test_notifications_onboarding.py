"""
Tests for:
  Notifications  — GET /notifications, PATCH /notifications/read-all,
                   PATCH /notifications/{id}/read
  Onboarding     — POST /onboarding/genres, GET /onboarding/suggestions,
                   POST /onboarding/complete
  User profile   — PATCH /users/me
"""
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


async def register_user(client: AsyncClient, username: str) -> dict:
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "pass1234",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


MOCK_MOVIE = {
    "tmdb_id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "release_date": "1999-10-15",
    "release_year": 1999,
    "poster_url": "https://image.tmdb.org/t/p/w500/fc.jpg",
    "backdrop_url": None,
    "overview": "An insomniac office worker forms an underground fight club.",
    "genres": [{"id": 18, "name": "Drama"}, {"id": 53, "name": "Thriller"}],
    "runtime": 139,
    "tmdb_rating": 8.4,
    "tmdb_vote_count": 22000,
}


# ════════════════════════════════════════════════════════════════
# NOTIFICATIONS
# ════════════════════════════════════════════════════════════════

async def test_get_notifications_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/notifications")
    assert resp.status_code == 401


async def test_get_notifications_empty(client: AsyncClient):
    tokens = await register_user(client, "notif_empty")
    resp = await client.get("/api/v1/notifications", headers=auth(tokens))
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["unread_count"] == 0


async def test_follow_creates_notification(client: AsyncClient):
    alice = await register_user(client, "alice_notif")
    bob = await register_user(client, "bob_notif")

    await client.post("/api/v1/users/alice_notif/follow", headers=auth(bob))

    resp = await client.get("/api/v1/notifications", headers=auth(alice))
    assert resp.status_code == 200
    data = resp.json()
    assert data["unread_count"] == 1
    notif = data["items"][0]
    assert notif["type"] == "follow"
    assert notif["actor"]["username"] == "bob_notif"
    assert notif["is_read"] is False


async def test_mark_single_notification_read(client: AsyncClient):
    alice = await register_user(client, "alice_read1")
    bob = await register_user(client, "bob_read1")

    await client.post("/api/v1/users/alice_read1/follow", headers=auth(bob))

    notifs = (await client.get("/api/v1/notifications", headers=auth(alice))).json()
    notif_id = notifs["items"][0]["id"]

    resp = await client.patch(
        f"/api/v1/notifications/{notif_id}/read", headers=auth(alice)
    )
    assert resp.status_code == 200

    updated = (await client.get("/api/v1/notifications", headers=auth(alice))).json()
    assert updated["unread_count"] == 0
    assert updated["items"][0]["is_read"] is True


async def test_mark_all_notifications_read(client: AsyncClient):
    alice = await register_user(client, "alice_readall")
    bob = await register_user(client, "bob_readall")
    charlie = await register_user(client, "charlie_readall")

    await client.post("/api/v1/users/alice_readall/follow", headers=auth(bob))
    await client.post("/api/v1/users/alice_readall/follow", headers=auth(charlie))

    before = (await client.get("/api/v1/notifications", headers=auth(alice))).json()
    assert before["unread_count"] == 2

    resp = await client.patch("/api/v1/notifications/read-all", headers=auth(alice))
    assert resp.status_code == 200

    after = (await client.get("/api/v1/notifications", headers=auth(alice))).json()
    assert after["unread_count"] == 0
    assert all(n["is_read"] for n in after["items"])


async def test_mark_read_all_requires_auth(client: AsyncClient):
    resp = await client.patch("/api/v1/notifications/read-all")
    assert resp.status_code == 401


async def test_notifications_not_visible_to_others(client: AsyncClient):
    """Notifications belong to the recipient, not the actor."""
    alice = await register_user(client, "alice_private")
    bob = await register_user(client, "bob_private")

    await client.post("/api/v1/users/alice_private/follow", headers=auth(bob))

    # Bob should have zero notifications (he's the actor, not recipient)
    bob_notifs = (await client.get("/api/v1/notifications", headers=auth(bob))).json()
    assert bob_notifs["items"] == []


# ════════════════════════════════════════════════════════════════
# ONBOARDING
# ════════════════════════════════════════════════════════════════

async def test_onboarding_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/onboarding/genres",
        json={"genre_ids": [28], "genre_names": ["Action"]},
    )
    assert resp.status_code == 401


async def test_save_genres(client: AsyncClient):
    tokens = await register_user(client, "ob_genres")
    resp = await client.post(
        "/api/v1/onboarding/genres",
        json={"genre_ids": [28, 18], "genre_names": ["Action", "Drama"]},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2


async def test_save_genres_replaces_existing(client: AsyncClient):
    """Calling POST /onboarding/genres twice should replace, not append."""
    tokens = await register_user(client, "ob_replace")
    await client.post(
        "/api/v1/onboarding/genres",
        json={"genre_ids": [28, 18], "genre_names": ["Action", "Drama"]},
        headers=auth(tokens),
    )
    resp = await client.post(
        "/api/v1/onboarding/genres",
        json={"genre_ids": [35], "genre_names": ["Comedy"]},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


async def test_onboarding_suggestions(client: AsyncClient):
    tokens = await register_user(client, "ob_suggest")
    await client.post(
        "/api/v1/onboarding/genres",
        json={"genre_ids": [28], "genre_names": ["Action"]},
        headers=auth(tokens),
    )
    resp = await client.get("/api/v1/onboarding/suggestions", headers=auth(tokens))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_complete_onboarding(client: AsyncClient):
    tokens = await register_user(client, "ob_complete")

    # Onboarding should start incomplete
    me_before = (await client.get("/api/v1/users/me", headers=auth(tokens))).json()
    assert me_before["onboarding_complete"] is False

    resp = await client.post("/api/v1/onboarding/complete", headers=auth(tokens))
    assert resp.status_code == 200

    me_after = (await client.get("/api/v1/users/me", headers=auth(tokens))).json()
    assert me_after["onboarding_complete"] is True


async def test_complete_onboarding_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/onboarding/complete")
    assert resp.status_code == 401


# ════════════════════════════════════════════════════════════════
# PATCH /users/me
# ════════════════════════════════════════════════════════════════

async def test_patch_me_requires_auth(client: AsyncClient):
    resp = await client.patch("/api/v1/users/me", json={"display_name": "New Name"})
    assert resp.status_code == 401


async def test_patch_me_display_name(client: AsyncClient):
    tokens = await register_user(client, "patch_me1")
    resp = await client.patch(
        "/api/v1/users/me",
        json={"display_name": "Cool Name"},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Cool Name"


async def test_patch_me_bio(client: AsyncClient):
    tokens = await register_user(client, "patch_me2")
    resp = await client.patch(
        "/api/v1/users/me",
        json={"bio": "Film enthusiast."},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    assert resp.json()["bio"] == "Film enthusiast."


async def test_patch_me_avatar_url(client: AsyncClient):
    tokens = await register_user(client, "patch_me3")
    resp = await client.patch(
        "/api/v1/users/me",
        json={"avatar_url": "https://example.com/avatar.jpg"},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    assert resp.json()["avatar_url"] == "https://example.com/avatar.jpg"


async def test_patch_me_partial_update(client: AsyncClient):
    """Only provided fields should change; others stay as-is."""
    tokens = await register_user(client, "patch_me4")

    # Set display name first
    await client.patch(
        "/api/v1/users/me",
        json={"display_name": "Original Name"},
        headers=auth(tokens),
    )

    # Update only bio
    resp = await client.patch(
        "/api/v1/users/me",
        json={"bio": "New bio only."},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_name"] == "Original Name"
    assert data["bio"] == "New bio only."


async def test_patch_me_returns_user_me_shape(client: AsyncClient):
    """Response should contain all UserMe fields."""
    tokens = await register_user(client, "patch_me5")
    resp = await client.patch(
        "/api/v1/users/me",
        json={"display_name": "Shape Test"},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    data = resp.json()
    for field in ("id", "username", "email", "display_name", "onboarding_complete",
                  "follower_count", "following_count", "created_at"):
        assert field in data, f"Missing field: {field}"
