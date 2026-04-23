"""
Tests for feed endpoints:
  GET /feed          (requires auth)
  GET /feed/global   (public)
  GET /feed/me       (requires auth – current user's own ratings)

Also tests follow/unfollow side-effects on the feed and
basic user-profile endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

MOCK_MOVIE_ME = {
    "tmdb_id": 550,
    "title": "Fight Club",
    "original_title": "Fight Club",
    "release_date": "1999-10-15",
    "release_year": 1999,
    "poster_url": "https://image.tmdb.org/t/p/w500/fc.jpg",
    "backdrop_url": None,
    "overview": "A story about soap.",
    "genres": [{"id": 18, "name": "Drama"}],
    "runtime": 139,
    "tmdb_rating": 8.8,
    "tmdb_vote_count": 25000,
}

MOCK_MOVIE_ME2 = {
    "tmdb_id": 278,
    "title": "The Shawshank Redemption",
    "original_title": "The Shawshank Redemption",
    "release_date": "1994-09-23",
    "release_year": 1994,
    "poster_url": None,
    "backdrop_url": None,
    "overview": "Two imprisoned men bond.",
    "genres": [{"id": 18, "name": "Drama"}],
    "runtime": 142,
    "tmdb_rating": 9.3,
    "tmdb_vote_count": 26000,
}


# ─── Helpers ───────────────────────────────────────────────────────────────

async def register_user(client: AsyncClient, username: str) -> dict:
    """Register and return {access_token, refresh_token}."""
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "password123",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# ─── Global feed ───────────────────────────────────────────────────────────

async def test_global_feed_public(client: AsyncClient):
    """Global feed is accessible without authentication."""
    resp = await client.get("/api/v1/feed/global")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "has_more" in data
    assert isinstance(data["items"], list)


async def test_global_feed_pagination(client: AsyncClient):
    resp = await client.get("/api/v1/feed/global", params={"limit": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) <= 5


# ─── Personal feed ─────────────────────────────────────────────────────────

async def test_feed_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/feed")
    assert resp.status_code == 401


async def test_feed_empty_for_new_user(client: AsyncClient):
    tokens = await register_user(client, "feedempty")
    resp = await client.get("/api/v1/feed", headers=auth(tokens))
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["has_more"] is False


async def test_feed_limit_parameter(client: AsyncClient):
    tokens = await register_user(client, "feedlimit")
    resp = await client.get("/api/v1/feed", headers=auth(tokens), params={"limit": 3})
    assert resp.status_code == 200


async def test_feed_invalid_limit(client: AsyncClient):
    tokens = await register_user(client, "feedinvalidlimit")
    resp = await client.get("/api/v1/feed", headers=auth(tokens), params={"limit": 100})
    # limit is capped at 50; FastAPI returns 422 for >50
    assert resp.status_code == 422


# ─── Follow / unfollow ─────────────────────────────────────────────────────

async def test_follow_user(client: AsyncClient):
    alice = await register_user(client, "alice_follow")
    bob = await register_user(client, "bob_follow")

    resp = await client.post(
        "/api/v1/users/bob_follow/follow",
        headers=auth(alice),
    )
    assert resp.status_code == 201


async def test_follow_self_rejected(client: AsyncClient):
    alice = await register_user(client, "alice_self")
    resp = await client.post(
        "/api/v1/users/alice_self/follow",
        headers=auth(alice),
    )
    assert resp.status_code == 400


async def test_double_follow_rejected(client: AsyncClient):
    alice = await register_user(client, "alice_dblf")
    bob = await register_user(client, "bob_dblf")

    await client.post("/api/v1/users/bob_dblf/follow", headers=auth(alice))
    resp = await client.post("/api/v1/users/bob_dblf/follow", headers=auth(alice))
    assert resp.status_code == 400


async def test_unfollow_user(client: AsyncClient):
    alice = await register_user(client, "alice_unf")
    bob = await register_user(client, "bob_unf")

    await client.post("/api/v1/users/bob_unf/follow", headers=auth(alice))

    resp = await client.delete(
        "/api/v1/users/bob_unf/follow",
        headers=auth(alice),
    )
    assert resp.status_code == 204


async def test_unfollow_without_following(client: AsyncClient):
    alice = await register_user(client, "alice_nof")
    bob = await register_user(client, "bob_nof")

    resp = await client.delete(
        "/api/v1/users/bob_nof/follow",
        headers=auth(alice),
    )
    assert resp.status_code == 404


# ─── Profile ───────────────────────────────────────────────────────────────

async def test_get_profile(client: AsyncClient):
    tokens = await register_user(client, "profileuser")
    resp = await client.get("/api/v1/users/profileuser")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "profileuser"
    assert "follower_count" in data
    assert "rating_count" in data


async def test_get_profile_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/users/doesnotexist9999")
    assert resp.status_code == 404


async def test_profile_is_following_flag(client: AsyncClient):
    alice = await register_user(client, "alice_flag")
    bob = await register_user(client, "bob_flag")

    # Before following
    resp = await client.get(
        "/api/v1/users/bob_flag",
        headers=auth(alice),
    )
    assert resp.json()["is_following"] is False

    # After following
    await client.post("/api/v1/users/bob_flag/follow", headers=auth(alice))
    resp = await client.get(
        "/api/v1/users/bob_flag",
        headers=auth(alice),
    )
    assert resp.json()["is_following"] is True


# ─── Ratings in profile ────────────────────────────────────────────────────

async def test_user_ratings_empty(client: AsyncClient):
    await register_user(client, "ratingempty")
    resp = await client.get("/api/v1/users/ratingempty/ratings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_follower_following_lists(client: AsyncClient):
    alice = await register_user(client, "alice_lists")
    bob = await register_user(client, "bob_lists")

    await client.post("/api/v1/users/bob_lists/follow", headers=auth(alice))

    # Alice following Bob → alice's following = [bob]
    resp = await client.get("/api/v1/users/alice_lists/following")
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert "bob_lists" in usernames

    # Bob's followers = [alice]
    resp = await client.get("/api/v1/users/bob_lists/followers")
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert "alice_lists" in usernames


# ─── My feed (GET /feed/me) ────────────────────────────────────────────────

async def test_my_feed_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/feed/me")
    assert resp.status_code == 401


async def test_my_feed_empty_for_new_user(client: AsyncClient):
    tokens = await register_user(client, "myfeedempty")
    resp = await client.get("/api/v1/feed/me", headers=auth(tokens))
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["has_more"] is False


async def test_my_feed_shows_own_ratings(client: AsyncClient):
    """User's own ratings appear in /feed/me."""
    tokens = await register_user(client, "myfeeduser")

    with patch("app.services.tmdb.get_movie", new=AsyncMock(return_value=MOCK_MOVIE_ME)):
        await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 550, "score": 8.0},
            headers=auth(tokens),
        )

    resp = await client.get("/api/v1/feed/me", headers=auth(tokens))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["movie"]["tmdb_id"] == 550
    assert item["score"] == 8.0
    assert "like_count" in item
    assert "liked_by_me" in item


async def test_my_feed_does_not_show_others_ratings(client: AsyncClient):
    """Other users' ratings do NOT appear in the requesting user's /feed/me."""
    alice = await register_user(client, "alice_myfeed")
    bob = await register_user(client, "bob_myfeed")

    with patch("app.services.tmdb.get_movie", new=AsyncMock(return_value=MOCK_MOVIE_ME2)):
        # Only Bob rates
        await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 278, "score": 9.0},
            headers=auth(bob),
        )

    # Alice's feed should be empty
    resp = await client.get("/api/v1/feed/me", headers=auth(alice))
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []


async def test_my_feed_limit_parameter(client: AsyncClient):
    tokens = await register_user(client, "myfeedlimit")
    resp = await client.get("/api/v1/feed/me", headers=auth(tokens), params={"limit": 5})
    assert resp.status_code == 200


async def test_my_feed_invalid_limit(client: AsyncClient):
    tokens = await register_user(client, "myfeedinvalidlimit")
    resp = await client.get("/api/v1/feed/me", headers=auth(tokens), params={"limit": 100})
    assert resp.status_code == 422
