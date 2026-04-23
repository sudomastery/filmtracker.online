import uuid
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rating import Rating
from app.models.rating_like import RatingLike
from app.models.movie import Movie
from app.models.user import User
from app.models.follow import Follow


async def get_feed(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    """
    Return paginated feed of ratings from users the current user follows.
    Uses cursor-based pagination on created_at + id.
    """
    # Get following IDs
    following_q = select(Follow.following_id).where(
        Follow.follower_id == current_user_id
    )

    # Main feed query
    query = (
        select(Rating, Movie, User)
        .join(Movie, Rating.movie_id == Movie.id)
        .join(User, Rating.user_id == User.id)
        .where(Rating.user_id.in_(following_q))
        .order_by(desc(Rating.created_at), desc(Rating.id))
        .limit(limit + 1)
    )

    if cursor:
        try:
            cursor_ts, cursor_id = cursor.split("_")
            from datetime import datetime, timezone
            cursor_dt = datetime.fromisoformat(cursor_ts)
            query = query.where(
                (Rating.created_at < cursor_dt)
                | (
                    and_(
                        Rating.created_at == cursor_dt,
                        Rating.id < uuid.UUID(cursor_id),
                    )
                )
            )
        except Exception:
            pass

    result = await db.execute(query)
    rows = result.fetchall()

    has_more = len(rows) > limit
    rows = rows[:limit]

    # Batch-fetch like counts and liked_by_me for this page
    rating_ids = [r.id for r, m, u in rows]
    like_counts: dict[uuid.UUID, int] = {}
    liked_by_me_ids: set[uuid.UUID] = set()

    if rating_ids:
        lc_result = await db.execute(
            select(RatingLike.rating_id, func.count().label("cnt"))
            .where(RatingLike.rating_id.in_(rating_ids))
            .group_by(RatingLike.rating_id)
        )
        like_counts = {row.rating_id: row.cnt for row in lc_result}

        lm_result = await db.execute(
            select(RatingLike.rating_id).where(
                RatingLike.user_id == current_user_id,
                RatingLike.rating_id.in_(rating_ids),
            )
        )
        liked_by_me_ids = {row.rating_id for row in lm_result}

    items = []
    for rating, movie, user in rows:
        items.append({
            "id": rating.id,
            "user": user,
            "movie": _movie_to_dict(movie),
            "score": float(rating.score) if rating.score else None,
            "review": rating.review,
            "contains_spoiler": rating.contains_spoiler,
            "watched_on": str(rating.watched_on) if rating.watched_on else None,
            "created_at": rating.created_at,
            "like_count": like_counts.get(rating.id, 0),
            "liked_by_me": rating.id in liked_by_me_ids,
        })

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last['created_at'].isoformat()}_{last['id']}"

    return {"items": items, "next_cursor": next_cursor, "has_more": has_more}


async def get_user_feed(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    """
    Return paginated feed of the current user's own ratings.
    Uses cursor-based pagination on created_at + id.
    """
    query = (
        select(Rating, Movie, User)
        .join(Movie, Rating.movie_id == Movie.id)
        .join(User, Rating.user_id == User.id)
        .where(Rating.user_id == current_user_id)
        .order_by(desc(Rating.created_at), desc(Rating.id))
        .limit(limit + 1)
    )

    if cursor:
        try:
            cursor_ts, cursor_id = cursor.split("_")
            from datetime import datetime, timezone
            cursor_dt = datetime.fromisoformat(cursor_ts)
            query = query.where(
                (Rating.created_at < cursor_dt)
                | (
                    and_(
                        Rating.created_at == cursor_dt,
                        Rating.id < uuid.UUID(cursor_id),
                    )
                )
            )
        except Exception:
            pass

    result = await db.execute(query)
    rows = result.fetchall()

    has_more = len(rows) > limit
    rows = rows[:limit]

    rating_ids = [r.id for r, m, u in rows]
    like_counts: dict[uuid.UUID, int] = {}
    liked_by_me_ids: set[uuid.UUID] = set()

    if rating_ids:
        lc_result = await db.execute(
            select(RatingLike.rating_id, func.count().label("cnt"))
            .where(RatingLike.rating_id.in_(rating_ids))
            .group_by(RatingLike.rating_id)
        )
        like_counts = {row.rating_id: row.cnt for row in lc_result}

        lm_result = await db.execute(
            select(RatingLike.rating_id).where(
                RatingLike.user_id == current_user_id,
                RatingLike.rating_id.in_(rating_ids),
            )
        )
        liked_by_me_ids = {row.rating_id for row in lm_result}

    items = []
    for rating, movie, user in rows:
        items.append({
            "id": rating.id,
            "user": user,
            "movie": _movie_to_dict(movie),
            "score": float(rating.score) if rating.score else None,
            "review": rating.review,
            "contains_spoiler": rating.contains_spoiler,
            "watched_on": str(rating.watched_on) if rating.watched_on else None,
            "created_at": rating.created_at,
            "like_count": like_counts.get(rating.id, 0),
            "liked_by_me": rating.id in liked_by_me_ids,
        })

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last['created_at'].isoformat()}_{last['id']}"

    return {"items": items, "next_cursor": next_cursor, "has_more": has_more}


async def get_global_feed(
    db: AsyncSession,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    query = (
        select(Rating, Movie, User)
        .join(Movie, Rating.movie_id == Movie.id)
        .join(User, Rating.user_id == User.id)
        .order_by(desc(Rating.created_at))
        .limit(limit + 1)
    )

    if cursor:
        try:
            from datetime import datetime
            cursor_dt = datetime.fromisoformat(cursor)
            query = query.where(Rating.created_at < cursor_dt)
        except Exception:
            pass

    result = await db.execute(query)
    rows = result.fetchall()

    has_more = len(rows) > limit
    rows = rows[:limit]

    # Batch-fetch like counts (no liked_by_me for global/unauthenticated feed)
    rating_ids = [r.id for r, m, u in rows]
    like_counts: dict[uuid.UUID, int] = {}

    if rating_ids:
        lc_result = await db.execute(
            select(RatingLike.rating_id, func.count().label("cnt"))
            .where(RatingLike.rating_id.in_(rating_ids))
            .group_by(RatingLike.rating_id)
        )
        like_counts = {row.rating_id: row.cnt for row in lc_result}

    items = []
    for rating, movie, user in rows:
        items.append({
            "id": rating.id,
            "user": user,
            "movie": _movie_to_dict(movie),
            "score": float(rating.score) if rating.score else None,
            "review": rating.review,
            "contains_spoiler": rating.contains_spoiler,
            "watched_on": str(rating.watched_on) if rating.watched_on else None,
            "created_at": rating.created_at,
            "like_count": like_counts.get(rating.id, 0),
            "liked_by_me": False,
        })

    next_cursor = items[-1]["created_at"].isoformat() if has_more and items else None
    return {"items": items, "next_cursor": next_cursor, "has_more": has_more}


def _movie_to_dict(movie: Movie) -> dict:
    return {
        "id": movie.id,
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "release_year": movie.release_year,
        "release_date": movie.release_date,
        "poster_url": movie.poster_url,
        "backdrop_url": movie.backdrop_url,
        "overview": movie.overview,
        "genres": movie.genres,
        "runtime": movie.runtime,
        "tmdb_rating": float(movie.tmdb_rating) if movie.tmdb_rating else None,
    }
