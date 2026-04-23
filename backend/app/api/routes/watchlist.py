import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, get_redis
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.movie import Movie
from app.models.watchlist import Watchlist
from app.schemas.movie import WatchlistCreate, WatchlistUpdate, WatchlistPublic
from app.services import tmdb as tmdb_service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

VALID_STATUSES = {"want_to_watch", "watching", "watched"}


@router.get("", response_model=list[dict])
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Watchlist, Movie)
        .join(Movie, Watchlist.movie_id == Movie.id)
        .where(Watchlist.user_id == current_user.id)
        .order_by(Watchlist.added_at.desc())
    )
    rows = result.fetchall()
    return [
        {
            "id": wl.id,
            "status": wl.status,
            "added_at": wl.added_at,
            "movie": {
                "id": m.id,
                "tmdb_id": m.tmdb_id,
                "title": m.title,
                "poster_url": m.poster_url,
                "release_year": m.release_year,
                "genres": m.genres,
                "tmdb_rating": float(m.tmdb_rating) if m.tmdb_rating else None,
            },
        }
        for wl, m in rows
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of {VALID_STATUSES}")

    # Ensure movie exists locally
    movie = await db.scalar(select(Movie).where(Movie.tmdb_id == payload.tmdb_id))
    if not movie:
        tmdb_data = await tmdb_service.get_movie(payload.tmdb_id, redis)
        movie = Movie(**tmdb_data)
        db.add(movie)
        await db.flush()
        await db.refresh(movie)

    existing = await db.scalar(
        select(Watchlist).where(
            Watchlist.user_id == current_user.id,
            Watchlist.movie_id == movie.id,
        )
    )
    if existing:
        existing.status = payload.status
        await db.flush()
        return {"id": existing.id, "status": existing.status}

    wl = Watchlist(user_id=current_user.id, movie_id=movie.id, status=payload.status)
    db.add(wl)
    await db.flush()
    await db.refresh(wl)
    return {"id": wl.id, "status": wl.status}


@router.patch("/{watchlist_id}")
async def update_watchlist_status(
    watchlist_id: uuid.UUID,
    payload: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of {VALID_STATUSES}")

    wl = await db.scalar(select(Watchlist).where(Watchlist.id == watchlist_id))
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    if wl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your watchlist")

    wl.status = payload.status
    await db.flush()
    return {"id": wl.id, "status": wl.status}


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    watchlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wl = await db.scalar(select(Watchlist).where(Watchlist.id == watchlist_id))
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    if wl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your watchlist")
    await db.delete(wl)
