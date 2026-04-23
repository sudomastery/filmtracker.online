import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db, get_redis
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.movie import Movie
from app.models.rating import Rating
from app.models.rating_like import RatingLike
from app.schemas.movie import RatingCreate, RatingPublic
from app.services import tmdb as tmdb_service

router = APIRouter(prefix="/ratings", tags=["ratings"])


async def _get_or_create_movie(tmdb_id: int, db: AsyncSession, redis) -> Movie:
    movie = await db.scalar(select(Movie).where(Movie.tmdb_id == tmdb_id))
    if not movie:
        tmdb_data = await tmdb_service.get_movie(tmdb_id, redis)
        movie = Movie(**tmdb_data)
        db.add(movie)
        await db.flush()
        await db.refresh(movie)
    return movie


@router.post("", response_model=RatingPublic, status_code=status.HTTP_201_CREATED)
async def create_or_update_rating(
    payload: RatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    movie = await _get_or_create_movie(payload.tmdb_id, db, redis)

    # Upsert — one rating per user per movie
    existing = await db.scalar(
        select(Rating).where(
            Rating.user_id == current_user.id,
            Rating.movie_id == movie.id,
        )
    )

    if existing:
        if payload.score is not None:
            existing.score = payload.score
        if payload.review is not None:
            existing.review = payload.review
        existing.contains_spoiler = payload.contains_spoiler
        if payload.watched_on is not None:
            existing.watched_on = payload.watched_on
        await db.flush()
        await db.refresh(existing)
        return existing
    else:
        rating = Rating(
            user_id=current_user.id,
            movie_id=movie.id,
            score=payload.score,
            review=payload.review,
            contains_spoiler=payload.contains_spoiler,
            watched_on=payload.watched_on,
        )
        db.add(rating)
        await db.flush()
        await db.refresh(rating)
        return rating


@router.delete("/{rating_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rating(
    rating_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rating = await db.scalar(select(Rating).where(Rating.id == rating_id))
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if rating.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your rating")
    await db.delete(rating)


@router.get("/me", response_model=list[RatingPublic])
async def my_ratings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import desc
    result = await db.execute(
        select(Rating)
        .where(Rating.user_id == current_user.id)
        .order_by(desc(Rating.created_at))
    )
    return result.scalars().all()


@router.post("/{rating_id}/like")
async def toggle_like(
    rating_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rating = await db.scalar(select(Rating).where(Rating.id == rating_id))
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")

    existing = await db.scalar(
        select(RatingLike).where(
            RatingLike.user_id == current_user.id,
            RatingLike.rating_id == rating_id,
        )
    )

    if existing:
        await db.delete(existing)
        await db.flush()
        liked = False
    else:
        db.add(RatingLike(user_id=current_user.id, rating_id=rating_id))
        # Notify the rating author (skip self-likes)
        if rating.user_id != current_user.id:
            from app.models.notification import Notification
            db.add(Notification(
                user_id=rating.user_id,
                actor_id=current_user.id,
                type="liked_review",
                entity_id=rating_id,
            ))
        await db.flush()
        liked = True

    like_count = await db.scalar(
        select(func.count()).where(RatingLike.rating_id == rating_id)
    )
    return {"liked": liked, "like_count": like_count or 0}
