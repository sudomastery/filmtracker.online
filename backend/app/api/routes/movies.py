import uuid
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db, get_redis
from app.models.movie import Movie
from app.models.rating import Rating
from app.services import tmdb as tmdb_service
from app.schemas.movie import MoviePublic

router = APIRouter(prefix="/movies", tags=["movies"])


async def _upsert_movie(tmdb_data: dict, db: AsyncSession) -> Movie:
    """Ensure the movie is in the local DB and return it."""
    existing = await db.scalar(
        select(Movie).where(Movie.tmdb_id == tmdb_data["tmdb_id"])
    )
    if existing:
        return existing
    movie = Movie(**{k: v for k, v in tmdb_data.items()})
    db.add(movie)
    await db.flush()
    await db.refresh(movie)
    return movie


async def _enrich(movie: Movie, db: AsyncSession) -> dict:
    stats = await db.execute(
        select(func.avg(Rating.score), func.count(Rating.id)).where(
            Rating.movie_id == movie.id
        )
    )
    avg, count = stats.one()
    d = {c.name: getattr(movie, c.name) for c in movie.__table__.columns}
    d["avg_user_rating"] = float(avg) if avg else None
    d["user_rating_count"] = count or 0
    return d


@router.get("/search", response_model=dict)
async def search_movies(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    return await tmdb_service.search_movies(q, page, redis)


@router.get("/trending", response_model=list[MoviePublic])
async def trending(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    movies_data = await tmdb_service.get_trending(redis)
    result = []
    for md in movies_data[:20]:
        movie = await _upsert_movie(md, db)
        enriched = await _enrich(movie, db)
        result.append(enriched)
    return result


@router.get("/genres")
async def get_genres(redis=Depends(get_redis)):
    return await tmdb_service.get_genres(redis)


@router.get("/{tmdb_id}", response_model=MoviePublic)
async def get_movie(
    tmdb_id: int,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    # Check local cache first
    existing = await db.scalar(select(Movie).where(Movie.tmdb_id == tmdb_id))
    if not existing:
        tmdb_data = await tmdb_service.get_movie(tmdb_id, redis)
        existing = await _upsert_movie(tmdb_data, db)
    return await _enrich(existing, db)


@router.get("/{tmdb_id}/ratings")
async def get_movie_ratings(
    tmdb_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    movie = await db.scalar(select(Movie).where(Movie.tmdb_id == tmdb_id))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    from app.models.user import User
    from sqlalchemy import desc
    offset = (page - 1) * limit
    result = await db.execute(
        select(Rating, User)
        .join(User, Rating.user_id == User.id)
        .where(Rating.movie_id == movie.id)
        .order_by(desc(Rating.created_at))
        .offset(offset)
        .limit(limit)
    )
    rows = result.fetchall()
    total = await db.scalar(
        select(func.count()).where(Rating.movie_id == movie.id)
    )

    items = []
    for rating, user in rows:
        items.append({
            "id": rating.id,
            "score": float(rating.score) if rating.score else None,
            "review": rating.review,
            "contains_spoiler": rating.contains_spoiler,
            "watched_on": str(rating.watched_on) if rating.watched_on else None,
            "created_at": rating.created_at,
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
            },
        })

    return {"items": items, "total": total, "page": page, "limit": limit}
