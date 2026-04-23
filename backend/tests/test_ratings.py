"""
Tests for ratings endpoints:
  POST   /ratings            — create or update
  DELETE /ratings/{id}       — delete
  GET    /ratings/me         — current user's ratings
  POST   /ratings/{id}/like  — toggle like / unlike
"""
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

# ─── Shared mock movie data ─────────────────────────────────────────────────

MOCK_MOVIE = {
    "tmdb_id": 155,
    "title": "The Dark Knight",
    "original_title": "The Dark Knight",
    "release_date": "2008-07-18",
    "release_year": 2008,
    "poster_url": "https://image.tmdb.org/t/p/w500/qJ2t.jpg",
    "backdrop_url": None,
    "overview": "Batman raises the stakes in his war on crime.",
    "genres": [{"id": 28, "name": "Action"}, {"id": 80, "name": "Crime"}],
    "runtime": 152,
    "tmdb_rating": 9.0,
    "tmdb_vote_count": 30000,
}


# ─── Helpers ────────────────────────────────────────────────────────────────

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


# ─── Auth guards ────────────────────────────────────────────────────────────

async def test_create_rating_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/ratings", json={"tmdb_id": 155, "score": 7.0})
    assert resp.status_code == 401


async def test_delete_rating_requires_auth(client: AsyncClient):
    resp = await client.delete("/api/v1/ratings/00000000-0000-0000-0000-000000000001")
    assert resp.status_code == 401


async def test_like_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/ratings/00000000-0000-0000-0000-000000000001/like"
    )
    assert resp.status_code == 401


# ─── Create ─────────────────────────────────────────────────────────────────

async def test_create_rating(client: AsyncClient):
    tokens = await register_user(client, "rater1")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        resp = await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 155, "score": 8.0, "review": "Great film!"},
            headers=auth(tokens),
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["score"] == 8.0
    assert data["review"] == "Great film!"
    assert "id" in data


async def test_create_rating_without_score(client: AsyncClient):
    """A review-only rating (no score) should be accepted."""
    tokens = await register_user(client, "rater_noscore")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        resp = await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 155, "review": "Interesting."},
            headers=auth(tokens),
        )
    assert resp.status_code == 201
    assert resp.json()["score"] is None


async def test_update_existing_rating(client: AsyncClient):
    """POST /ratings with the same tmdb_id should update, not duplicate."""
    tokens = await register_user(client, "rater2")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 155, "score": 6.0},
            headers=auth(tokens),
        )
        resp = await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 155, "score": 9.0, "review": "Changed my mind!"},
            headers=auth(tokens),
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["score"] == 9.0
    assert data["review"] == "Changed my mind!"

    # Only one rating should exist
    me = await client.get("/api/v1/ratings/me", headers=auth(tokens))
    assert len(me.json()) == 1


# ─── Delete ─────────────────────────────────────────────────────────────────

async def test_delete_rating(client: AsyncClient):
    tokens = await register_user(client, "delrater")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        created = (
            await client.post(
                "/api/v1/ratings",
                json={"tmdb_id": 155, "score": 7.0},
                headers=auth(tokens),
            )
        ).json()

    resp = await client.delete(
        f"/api/v1/ratings/{created['id']}", headers=auth(tokens)
    )
    assert resp.status_code == 204

    # Confirm gone
    me = await client.get("/api/v1/ratings/me", headers=auth(tokens))
    assert me.json() == []


async def test_delete_other_users_rating_forbidden(client: AsyncClient):
    alice = await register_user(client, "alice_del")
    bob = await register_user(client, "bob_del")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        alice_rating = (
            await client.post(
                "/api/v1/ratings",
                json={"tmdb_id": 155, "score": 7.0},
                headers=auth(alice),
            )
        ).json()

    resp = await client.delete(
        f"/api/v1/ratings/{alice_rating['id']}", headers=auth(bob)
    )
    assert resp.status_code == 403


async def test_delete_nonexistent_rating(client: AsyncClient):
    tokens = await register_user(client, "delnonexist")
    resp = await client.delete(
        "/api/v1/ratings/00000000-0000-0000-0000-000000000001",
        headers=auth(tokens),
    )
    assert resp.status_code == 404


# ─── GET /ratings/me ────────────────────────────────────────────────────────

async def test_get_my_ratings_empty(client: AsyncClient):
    tokens = await register_user(client, "myratings_empty")
    resp = await client.get("/api/v1/ratings/me", headers=auth(tokens))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_my_ratings_returns_created(client: AsyncClient):
    tokens = await register_user(client, "myratings_user")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 155, "score": 7.5},
            headers=auth(tokens),
        )

    resp = await client.get("/api/v1/ratings/me", headers=auth(tokens))
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["score"] == 7.5


# ─── Like / unlike ──────────────────────────────────────────────────────────

async def test_like_rating(client: AsyncClient):
    alice = await register_user(client, "alice_like")
    bob = await register_user(client, "bob_like")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        rating = (
            await client.post(
                "/api/v1/ratings",
                json={"tmdb_id": 155, "score": 8.0},
                headers=auth(alice),
            )
        ).json()

    resp = await client.post(
        f"/api/v1/ratings/{rating['id']}/like", headers=auth(bob)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["liked"] is True
    assert data["like_count"] == 1


async def test_unlike_rating(client: AsyncClient):
    alice = await register_user(client, "alice_unlike")
    bob = await register_user(client, "bob_unlike")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        rating = (
            await client.post(
                "/api/v1/ratings",
                json={"tmdb_id": 155, "score": 8.0},
                headers=auth(alice),
            )
        ).json()

    # Like
    await client.post(f"/api/v1/ratings/{rating['id']}/like", headers=auth(bob))
    # Unlike
    resp = await client.post(
        f"/api/v1/ratings/{rating['id']}/like", headers=auth(bob)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["liked"] is False
    assert data["like_count"] == 0


async def test_like_creates_notification(client: AsyncClient):
    alice = await register_user(client, "alice_lnotif")
    bob = await register_user(client, "bob_lnotif")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        rating = (
            await client.post(
                "/api/v1/ratings",
                json={"tmdb_id": 155, "score": 8.0},
                headers=auth(alice),
            )
        ).json()

    await client.post(f"/api/v1/ratings/{rating['id']}/like", headers=auth(bob))

    notif_resp = await client.get("/api/v1/notifications", headers=auth(alice))
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()["items"]
    liked_notifs = [n for n in notifs if n["type"] == "liked_review"]
    assert len(liked_notifs) == 1
    assert liked_notifs[0]["actor"]["username"] == "bob_lnotif"


async def test_self_like_no_notification(client: AsyncClient):
    """Liking your own rating must not create a notification."""
    alice = await register_user(client, "alice_selflike")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        rating = (
            await client.post(
                "/api/v1/ratings",
                json={"tmdb_id": 155, "score": 8.0},
                headers=auth(alice),
            )
        ).json()

    await client.post(f"/api/v1/ratings/{rating['id']}/like", headers=auth(alice))

    notif_resp = await client.get("/api/v1/notifications", headers=auth(alice))
    assert notif_resp.json()["items"] == []


async def test_like_nonexistent_rating(client: AsyncClient):
    tokens = await register_user(client, "likenonexist")
    resp = await client.post(
        "/api/v1/ratings/00000000-0000-0000-0000-000000000001/like",
        headers=auth(tokens),
    )
    assert resp.status_code == 404


async def test_like_count_in_feed(client: AsyncClient):
    """Feed items should expose like_count and liked_by_me."""
    alice = await register_user(client, "alice_feedlike")
    bob = await register_user(client, "bob_feedlike")

    # Bob follows Alice
    await client.post("/api/v1/users/alice_feedlike/follow", headers=auth(bob))

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        rating = (
            await client.post(
                "/api/v1/ratings",
                json={"tmdb_id": 155, "score": 8.0},
                headers=auth(alice),
            )
        ).json()

    # Bob likes Alice's rating
    await client.post(f"/api/v1/ratings/{rating['id']}/like", headers=auth(bob))

    feed = (await client.get("/api/v1/feed", headers=auth(bob))).json()
    assert len(feed["items"]) == 1
    item = feed["items"][0]
    assert item["like_count"] == 1
    assert item["liked_by_me"] is True
