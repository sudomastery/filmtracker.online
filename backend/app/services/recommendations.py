import uuid
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.rating import Rating
from app.models.movie import Movie
from app.models.follow import Follow
from app.models.genre_preference import UserGenrePreference


async def get_suggested_users(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    genre_ids: list[int],
    limit: int = 20,
) -> list[dict]:
    """
    Find users who have rated movies in the given genres highly.
    Excludes the current user and already-followed users.
    """
    if not genre_ids:
        # Fall back to most active users
        query = (
            select(User, func.count(Rating.id).label("rating_count"))
            .join(Rating, Rating.user_id == User.id)
            .where(User.id != current_user_id)
            .group_by(User.id)
            .order_by(func.count(Rating.id).desc())
            .limit(limit)
        )
        result = await db.execute(query)
        rows = result.fetchall()
        return [_user_row(u, rc, []) for u, rc in rows]

    genre_ids_str = ",".join(str(g) for g in genre_ids)

    raw_sql = text(f"""
        SELECT
            u.id,
            u.username,
            u.display_name,
            u.avatar_url,
            u.bio,
            u.created_at,
            COUNT(DISTINCT r.id) AS rating_count,
            AVG(r.score)         AS avg_score
        FROM users u
        JOIN ratings r  ON r.user_id = u.id
        JOIN movies  m  ON m.id = r.movie_id
        CROSS JOIN LATERAL jsonb_array_elements(m.genres) AS genre_elem
        WHERE (genre_elem->>'id')::int = ANY(ARRAY[{genre_ids_str}])
          AND r.score >= 6
          AND u.id != :current_user_id
          AND u.id NOT IN (
              SELECT following_id FROM follows WHERE follower_id = :current_user_id
          )
        GROUP BY u.id
        HAVING COUNT(DISTINCT r.id) >= 1
        ORDER BY rating_count DESC
        LIMIT :limit
    """)

    result = await db.execute(
        raw_sql,
        {"current_user_id": str(current_user_id), "limit": limit},
    )
    rows = result.fetchall()

    suggested = []
    for row in rows:
        suggested.append({
            "id": row.id,
            "username": row.username,
            "display_name": row.display_name,
            "avatar_url": row.avatar_url,
            "bio": row.bio,
            "created_at": row.created_at,
            "rating_count": row.rating_count,
            "avg_score": float(row.avg_score) if row.avg_score else None,
        })
    return suggested


def _user_row(user: User, rating_count: int, genres: list) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "created_at": user.created_at,
        "rating_count": rating_count,
        "avg_score": None,
    }
