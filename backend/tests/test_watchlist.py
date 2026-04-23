"""
Tests for watchlist endpoints:
  GET    /watchlist
  POST   /watchlist
  PATCH  /watchlist/{id}
  DELETE /watchlist/{id}
"""
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient

MOCK_MOVIE = {
    "tmdb_id": 603,
    "title": "The Matrix",
    "original_title": "The Matrix",
    "release_date": "1999-03-31",
    "release_year": 1999,
    "poster_url": "https://image.tmdb.org/t/p/w500/matrix.jpg",
    "backdrop_url": None,
    "overview": "A computer hacker learns about the true nature of reality.",
    "genres": [{"id": 28, "name": "Action"}, {"id": 878, "name": "Science Fiction"}],
    "runtime": 136,
    "tmdb_rating": 8.7,
    "tmdb_vote_count": 25000,
}

MOCK_MOVIE_2 = {
    "tmdb_id": 13,
    "title": "Forrest Gump",
    "original_title": "Forrest Gump",
    "release_date": "1994-07-06",
    "release_year": 1994,
    "poster_url": "https://image.tmdb.org/t/p/w500/fg.jpg",
    "backdrop_url": None,
    "overview": "The presidencies of Kennedy and Johnson.",
    "genres": [{"id": 35, "name": "Comedy"}, {"id": 18, "name": "Drama"}],
    "runtime": 142,
    "tmdb_rating": 8.5,
    "tmdb_vote_count": 20000,
}


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

async def test_get_watchlist_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/watchlist")
    assert resp.status_code == 401


async def test_add_to_watchlist_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/watchlist", json={"tmdb_id": 603})
    assert resp.status_code == 401


async def test_update_watchlist_requires_auth(client: AsyncClient):
    resp = await client.patch(
        "/api/v1/watchlist/00000000-0000-0000-0000-000000000001",
        json={"status": "watched"},
    )
    assert resp.status_code == 401


async def test_delete_watchlist_requires_auth(client: AsyncClient):
    resp = await client.delete(
        "/api/v1/watchlist/00000000-0000-0000-0000-000000000001"
    )
    assert resp.status_code == 401


# ─── Empty list ─────────────────────────────────────────────────────────────

async def test_get_watchlist_empty(client: AsyncClient):
    tokens = await register_user(client, "wl_empty")
    resp = await client.get("/api/v1/watchlist", headers=auth(tokens))
    assert resp.status_code == 200
    assert resp.json() == []


# ─── Add ────────────────────────────────────────────────────────────────────

async def test_add_to_watchlist(client: AsyncClient):
    tokens = await register_user(client, "wl_add")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        resp = await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 603, "status": "want_to_watch"},
            headers=auth(tokens),
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "want_to_watch"
    assert "id" in data


async def test_add_to_watchlist_default_status(client: AsyncClient):
    """Omitting status should default to want_to_watch."""
    tokens = await register_user(client, "wl_default")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        resp = await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 603},
            headers=auth(tokens),
        )
    assert resp.status_code == 201
    assert resp.json()["status"] == "want_to_watch"


async def test_add_invalid_status_rejected(client: AsyncClient):
    tokens = await register_user(client, "wl_badstatus")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        resp = await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 603, "status": "not_a_real_status"},
            headers=auth(tokens),
        )
    assert resp.status_code == 400


async def test_add_duplicate_updates_status(client: AsyncClient):
    """Adding the same movie twice should update status, not duplicate."""
    tokens = await register_user(client, "wl_dup")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 603, "status": "want_to_watch"},
            headers=auth(tokens),
        )
        resp = await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 603, "status": "watched"},
            headers=auth(tokens),
        )
    assert resp.status_code == 201
    assert resp.json()["status"] == "watched"

    # Only one entry
    wl = await client.get("/api/v1/watchlist", headers=auth(tokens))
    assert len(wl.json()) == 1


async def test_watchlist_contains_movie_details(client: AsyncClient):
    tokens = await register_user(client, "wl_details")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 603, "status": "want_to_watch"},
            headers=auth(tokens),
        )

    wl = await client.get("/api/v1/watchlist", headers=auth(tokens))
    items = wl.json()
    assert len(items) == 1
    movie = items[0]["movie"]
    assert movie["tmdb_id"] == 603
    assert movie["title"] == "The Matrix"


# ─── PATCH ──────────────────────────────────────────────────────────────────

async def test_update_watchlist_status(client: AsyncClient):
    tokens = await register_user(client, "wl_patch")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        item = (
            await client.post(
                "/api/v1/watchlist",
                json={"tmdb_id": 603, "status": "want_to_watch"},
                headers=auth(tokens),
            )
        ).json()

    resp = await client.patch(
        f"/api/v1/watchlist/{item['id']}",
        json={"status": "watching"},
        headers=auth(tokens),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "watching"


async def test_update_other_users_watchlist_forbidden(client: AsyncClient):
    alice = await register_user(client, "alice_wl")
    bob = await register_user(client, "bob_wl")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        item = (
            await client.post(
                "/api/v1/watchlist",
                json={"tmdb_id": 603, "status": "want_to_watch"},
                headers=auth(alice),
            )
        ).json()

    resp = await client.patch(
        f"/api/v1/watchlist/{item['id']}",
        json={"status": "watched"},
        headers=auth(bob),
    )
    assert resp.status_code == 403


async def test_update_nonexistent_watchlist(client: AsyncClient):
    tokens = await register_user(client, "wl_nonexist")
    resp = await client.patch(
        "/api/v1/watchlist/00000000-0000-0000-0000-000000000001",
        json={"status": "watched"},
        headers=auth(tokens),
    )
    assert resp.status_code == 404


# ─── DELETE ─────────────────────────────────────────────────────────────────

async def test_delete_watchlist_item(client: AsyncClient):
    tokens = await register_user(client, "wl_del")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        item = (
            await client.post(
                "/api/v1/watchlist",
                json={"tmdb_id": 603, "status": "want_to_watch"},
                headers=auth(tokens),
            )
        ).json()

    resp = await client.delete(
        f"/api/v1/watchlist/{item['id']}", headers=auth(tokens)
    )
    assert resp.status_code == 204

    wl = await client.get("/api/v1/watchlist", headers=auth(tokens))
    assert wl.json() == []


async def test_delete_other_users_watchlist_forbidden(client: AsyncClient):
    alice = await register_user(client, "alice_wldel")
    bob = await register_user(client, "bob_wldel")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        item = (
            await client.post(
                "/api/v1/watchlist",
                json={"tmdb_id": 603, "status": "want_to_watch"},
                headers=auth(alice),
            )
        ).json()

    resp = await client.delete(
        f"/api/v1/watchlist/{item['id']}", headers=auth(bob)
    )
    assert resp.status_code == 403


async def test_delete_nonexistent_watchlist(client: AsyncClient):
    tokens = await register_user(client, "wl_delnonexist")
    resp = await client.delete(
        "/api/v1/watchlist/00000000-0000-0000-0000-000000000001",
        headers=auth(tokens),
    )
    assert resp.status_code == 404


# ─── Multiple items ─────────────────────────────────────────────────────────

async def test_watchlist_multiple_movies(client: AsyncClient):
    tokens = await register_user(client, "wl_multi")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock) as mock_tmdb:
        mock_tmdb.side_effect = [MOCK_MOVIE, MOCK_MOVIE_2]
        await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 603, "status": "want_to_watch"},
            headers=auth(tokens),
        )
        await client.post(
            "/api/v1/watchlist",
            json={"tmdb_id": 13, "status": "watched"},
            headers=auth(tokens),
        )

    wl = await client.get("/api/v1/watchlist", headers=auth(tokens))
    items = wl.json()
    assert len(items) == 2
    titles = {i["movie"]["title"] for i in items}
    assert "The Matrix" in titles
    assert "Forrest Gump" in titles
