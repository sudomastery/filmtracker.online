import re
import json
import uuid
from rapidfuzz import fuzz
from app.services import tmdb as tmdb_service


def parse_lines(content: str) -> list[str]:
    """Parse TXT file content into a list of movie title strings."""
    lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def extract_title_year(line: str) -> tuple[str, int | None]:
    """Extract title and optional year from a line like 'The Godfather 1972'."""
    match = re.search(r'\b(19[0-9]{2}|20[0-2][0-9])\b', line)
    if match:
        year = int(match.group())
        title = (line[: match.start()] + line[match.end() :]).strip(" -()[]")
        return title, year
    return line.strip(), None


def score_result(query: str, result_title: str, query_year: int | None, result_year: int | None) -> int:
    base = fuzz.token_sort_ratio(query.lower(), result_title.lower())
    if query_year and result_year and query_year == result_year:
        base = min(100, base + 10)
    return base


async def process_import(job_id: str, lines: list[str], user_id: str, redis, db):
    """Background processing — called from Celery task."""
    from app.models.movie import Movie
    from app.models.watchlist import Watchlist
    from sqlalchemy import select

    total = len(lines)
    results = []

    await redis.hset(f"import:{job_id}", mapping={
        "status": "processing",
        "total": total,
        "processed": 0,
        "matched": 0,
        "unmatched": 0,
    })

    matched_count = 0
    unmatched_count = 0

    for i, line in enumerate(lines):
        title, year = extract_title_year(line)
        try:
            search_data = await tmdb_service.search_movies(title, redis=redis)
            candidates = search_data.get("results", [])

            best = None
            best_score = 0
            for candidate in candidates[:5]:
                c_year = candidate.get("release_year")
                score = score_result(title, candidate["title"], year, c_year)
                if score > best_score:
                    best_score = score
                    best = candidate

            if best and best_score >= 70:
                # Upsert movie into local DB
                existing = await db.scalar(
                    select(Movie).where(Movie.tmdb_id == best["tmdb_id"])
                )
                if not existing:
                    movie = Movie(**{k: v for k, v in best.items() if k != "avg_user_rating"})
                    db.add(movie)
                    await db.flush()
                    movie_id = movie.id
                else:
                    movie_id = existing.id

                # Add to watchlist (want_to_watch) if not already there
                existing_wl = await db.scalar(
                    select(Watchlist).where(
                        Watchlist.user_id == uuid.UUID(user_id),
                        Watchlist.movie_id == movie_id,
                    )
                )
                if not existing_wl:
                    db.add(Watchlist(
                        user_id=uuid.UUID(user_id),
                        movie_id=movie_id,
                        status="want_to_watch",
                    ))

                await db.commit()

                results.append({
                    "line": line,
                    "matched": True,
                    "tmdb_id": best["tmdb_id"],
                    "title": best["title"],
                    "poster_url": best.get("poster_url"),
                    "release_year": best.get("release_year"),
                    "confidence": best_score,
                })
                matched_count += 1
            else:
                results.append({"line": line, "matched": False})
                unmatched_count += 1

        except Exception:
            results.append({"line": line, "matched": False})
            unmatched_count += 1

        await redis.hset(f"import:{job_id}", mapping={
            "processed": i + 1,
            "matched": matched_count,
            "unmatched": unmatched_count,
        })

    await redis.hset(f"import:{job_id}", "status", "done")
    await redis.setex(f"import:{job_id}:results", 3600, json.dumps(results))
