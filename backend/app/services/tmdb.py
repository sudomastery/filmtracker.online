import json
import httpx
from app.core.config import settings

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p"
HEADERS = {"Authorization": f"Bearer {settings.TMDB_READ_ACCESS_TOKEN}"}

# TTLs in seconds
TTL_MOVIE = 86400        # 24h
TTL_SEARCH = 3600        # 1h
TTL_TRENDING = 21600     # 6h
TTL_GENRES = 604800      # 7d


def _poster(path: str | None, size: str = "w500") -> str | None:
    if not path:
        return None
    return f"{TMDB_IMAGE_BASE}/{size}{path}"


def _normalize_movie(data: dict) -> dict:
    genres = data.get("genres") or [
        {"id": g["id"], "name": g["name"]}
        for g in data.get("genre_ids", [])
        if isinstance(g, dict)
    ]
    if not genres and "genre_ids" in data:
        genres = [{"id": gid} for gid in data["genre_ids"]]

    release_date = data.get("release_date", "")
    release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 else None

    return {
        "tmdb_id": data["id"],
        "title": data.get("title") or data.get("name", ""),
        "original_title": data.get("original_title"),
        "release_date": release_date or None,
        "release_year": release_year,
        "poster_url": _poster(data.get("poster_path")),
        "backdrop_url": _poster(data.get("backdrop_path"), "w1280"),
        "overview": data.get("overview"),
        "genres": genres or None,
        "runtime": data.get("runtime"),
        "tmdb_rating": data.get("vote_average"),
        "tmdb_vote_count": data.get("vote_count"),
    }


async def get_movie(tmdb_id: int, redis) -> dict:
    cache_key = f"tmdb:movie:{tmdb_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{TMDB_BASE}/movie/{tmdb_id}", headers=HEADERS)
        r.raise_for_status()
        data = r.json()

    normalized = _normalize_movie(data)
    await redis.setex(cache_key, TTL_MOVIE, json.dumps(normalized))
    return normalized


async def search_movies(query: str, page: int = 1, redis=None) -> dict:
    cache_key = f"tmdb:search:{query}:{page}"
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{TMDB_BASE}/search/movie",
            headers=HEADERS,
            params={"query": query, "page": page, "include_adult": False},
        )
        r.raise_for_status()
        raw = r.json()

    results = [_normalize_movie(m) for m in raw.get("results", [])]
    data = {
        "results": results,
        "total_results": raw.get("total_results", 0),
        "total_pages": raw.get("total_pages", 1),
        "page": page,
    }

    if redis:
        await redis.setex(cache_key, TTL_SEARCH, json.dumps(data))
    return data


async def get_trending(redis) -> list[dict]:
    cache_key = "tmdb:trending:week"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{TMDB_BASE}/trending/movie/week", headers=HEADERS
        )
        r.raise_for_status()
        raw = r.json()

    results = [_normalize_movie(m) for m in raw.get("results", [])]
    await redis.setex(cache_key, TTL_TRENDING, json.dumps(results))
    return results


async def get_genres(redis) -> list[dict]:
    cache_key = "tmdb:genres"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{TMDB_BASE}/genre/movie/list", headers=HEADERS
        )
        r.raise_for_status()
        data = r.json().get("genres", [])

    await redis.setex(cache_key, TTL_GENRES, json.dumps(data))
    return data
