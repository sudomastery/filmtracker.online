"""
Tests for movie endpoints:
  GET /movies/{tmdb_id}
  GET /movies/{tmdb_id}/ratings
  GET /movies/search
  GET /movies/trending
  GET /movies/genres
"""
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient

MOCK_MOVIE = {
    "tmdb_id": 238,
    "title": "The Godfather",
    "original_title": "The Godfather",
    "release_date": "1972-03-24",
    "release_year": 1972,
    "poster_url": "https://image.tmdb.org/t/p/w500/gf.jpg",
    "backdrop_url": None,
    "overview": "The aging patriarch of an organized crime dynasty.",
    "genres": [{"id": 18, "name": "Drama"}, {"id": 80, "name": "Crime"}],
    "runtime": 175,
    "tmdb_rating": 9.2,
    "tmdb_vote_count": 18000,
}

MOCK_SEARCH_RESULT = {
    "results": [
        {
            "tmdb_id": 238,
            "title": "The Godfather",
            "release_year": 1972,
            "poster_url": "https://image.tmdb.org/t/p/w500/gf.jpg",
        }
    ],
    "total_results": 1,
    "total_pages": 1,
}

MOCK_GENRES = [
    {"id": 28, "name": "Action"},
    {"id": 18, "name": "Drama"},
    {"id": 35, "name": "Comedy"},
]


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


# ─── GET /movies/{tmdb_id} ──────────────────────────────────────────────────

async def test_get_movie_fetches_from_tmdb(client: AsyncClient):
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        resp = await client.get("/api/v1/movies/238")

    assert resp.status_code == 200
    data = resp.json()
    assert data["tmdb_id"] == 238
    assert data["title"] == "The Godfather"
    assert "avg_user_rating" in data
    assert "user_rating_count" in data
    assert data["user_rating_count"] == 0


async def test_get_movie_served_from_db_second_request(client: AsyncClient):
    """Second request for the same movie must NOT call TMDB again."""
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE) as mock_tmdb:
        await client.get("/api/v1/movies/238")
        await client.get("/api/v1/movies/238")
        assert mock_tmdb.call_count == 1


async def test_get_movie_avg_rating_reflects_ratings(client: AsyncClient):
    tokens = await register_user(client, "movie_rater")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        # Seed movie and post a rating
        await client.get("/api/v1/movies/238")
        await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 238, "score": 10.0},
            headers=auth(tokens),
        )

    resp = await client.get("/api/v1/movies/238")
    data = resp.json()
    assert data["user_rating_count"] == 1
    assert data["avg_user_rating"] == 10.0


# ─── GET /movies/{tmdb_id}/ratings ─────────────────────────────────────────

async def test_get_movie_ratings_404_when_not_in_db(client: AsyncClient):
    resp = await client.get("/api/v1/movies/99999999/ratings")
    assert resp.status_code == 404


async def test_get_movie_ratings_empty(client: AsyncClient):
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        await client.get("/api/v1/movies/238")

    resp = await client.get("/api/v1/movies/238/ratings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_get_movie_ratings_returns_posted_ratings(client: AsyncClient):
    tokens = await register_user(client, "ratings_reader")
    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 238, "score": 8.5, "review": "A masterpiece."},
            headers=auth(tokens),
        )

    resp = await client.get("/api/v1/movies/238/ratings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["score"] == 8.5
    assert item["review"] == "A masterpiece."
    assert item["user"]["username"] == "ratings_reader"


async def test_get_movie_ratings_pagination(client: AsyncClient):
    tokens = await register_user(client, "pager1")

    with patch("app.services.tmdb.get_movie", new_callable=AsyncMock, return_value=MOCK_MOVIE):
        await client.post(
            "/api/v1/ratings",
            json={"tmdb_id": 238, "score": 7.0},
            headers=auth(tokens),
        )

    resp = await client.get("/api/v1/movies/238/ratings?page=1&limit=1")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["limit"] == 1


# ─── GET /movies/search ─────────────────────────────────────────────────────

async def test_search_movies(client: AsyncClient):
    with patch(
        "app.services.tmdb.search_movies",
        new_callable=AsyncMock,
        return_value=MOCK_SEARCH_RESULT,
    ):
        resp = await client.get("/api/v1/movies/search?q=godfather")

    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert data["total_results"] == 1


async def test_search_movies_requires_query(client: AsyncClient):
    resp = await client.get("/api/v1/movies/search")
    assert resp.status_code == 422


# ─── GET /movies/trending ───────────────────────────────────────────────────

async def test_trending_movies(client: AsyncClient):
    with patch(
        "app.services.tmdb.get_trending",
        new_callable=AsyncMock,
        return_value=[MOCK_MOVIE],
    ):
        resp = await client.get("/api/v1/movies/trending")

    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["tmdb_id"] == 238


# ─── GET /movies/genres ─────────────────────────────────────────────────────

async def test_get_genres(client: AsyncClient):
    with patch(
        "app.services.tmdb.get_genres",
        new_callable=AsyncMock,
        return_value=MOCK_GENRES,
    ):
        resp = await client.get("/api/v1/movies/genres")

    assert resp.status_code == 200
    genres = resp.json()
    assert len(genres) == 3
    names = [g["name"] for g in genres]
    assert "Action" in names
    assert "Drama" in names
