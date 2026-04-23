import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.core.database import get_db
from app.api.dependencies.auth import get_current_user, get_optional_user
from app.models.user import User
from app.models.follow import Follow
from app.models.rating import Rating
from app.models.movie import Movie
from app.schemas.user import UserProfile, UserMe, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserMe)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    follower_count = await db.scalar(
        select(func.count()).where(Follow.following_id == current_user.id)
    )
    following_count = await db.scalar(
        select(func.count()).where(Follow.follower_id == current_user.id)
    )
    return UserMe(
        **{c.name: getattr(current_user, c.name) for c in current_user.__table__.columns},
        follower_count=follower_count or 0,
        following_count=following_count or 0,
    )


@router.patch("/me", response_model=UserMe)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.flush()
    await db.refresh(current_user)

    follower_count = await db.scalar(
        select(func.count()).where(Follow.following_id == current_user.id)
    )
    following_count = await db.scalar(
        select(func.count()).where(Follow.follower_id == current_user.id)
    )
    return UserMe(
        **{c.name: getattr(current_user, c.name) for c in current_user.__table__.columns},
        follower_count=follower_count or 0,
        following_count=following_count or 0,
    )


@router.get("/{username}/ratings")
async def get_user_ratings(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user = await db.scalar(select(User).where(User.username == username.lower()))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(Rating, Movie)
        .join(Movie, Rating.movie_id == Movie.id)
        .where(Rating.user_id == user.id)
        .order_by(desc(Rating.created_at))
    )
    rows = result.fetchall()

    items = [
        {
            "id": r.id,
            "score": float(r.score) if r.score is not None else None,
            "review": r.review,
            "contains_spoiler": r.contains_spoiler,
            "watched_on": str(r.watched_on) if r.watched_on else None,
            "created_at": r.created_at,
            "movie": {
                "tmdb_id": m.tmdb_id,
                "title": m.title,
                "poster_url": m.poster_url,
                "release_year": m.release_year,
            },
        }
        for r, m in rows
    ]

    return {"items": items, "total": len(items)}


@router.get("/{username}", response_model=UserProfile)
async def get_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    user = await db.scalar(select(User).where(User.username == username.lower()))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    follower_count = await db.scalar(
        select(func.count()).where(Follow.following_id == user.id)
    ) or 0
    following_count = await db.scalar(
        select(func.count()).where(Follow.follower_id == user.id)
    ) or 0
    rating_count = await db.scalar(
        select(func.count()).where(Rating.user_id == user.id)
    ) or 0

    is_following = False
    if current_user:
        is_following = bool(
            await db.scalar(
                select(Follow).where(
                    Follow.follower_id == current_user.id,
                    Follow.following_id == user.id,
                )
            )
        )

    return UserProfile(
        **{c.name: getattr(user, c.name) for c in user.__table__.columns},
        follower_count=follower_count,
        following_count=following_count,
        rating_count=rating_count,
        is_following=is_following,
    )


@router.post("/{username}/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(select(User).where(User.username == username.lower()))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    existing = await db.scalar(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == target.id,
        )
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already following")

    db.add(Follow(follower_id=current_user.id, following_id=target.id))

    from app.models.notification import Notification
    db.add(Notification(
        user_id=target.id,
        actor_id=current_user.id,
        type="follow",
    ))

    return {"detail": f"Now following {username}"}


@router.delete("/{username}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(select(User).where(User.username == username.lower()))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    follow = await db.scalar(
        select(Follow).where(
            Follow.follower_id == current_user.id,
            Follow.following_id == target.id,
        )
    )
    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")

    await db.delete(follow)


@router.get("/{username}/followers", response_model=list[UserProfile])
async def get_followers(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(select(User).where(User.username == username.lower()))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(User).join(Follow, Follow.follower_id == User.id).where(
            Follow.following_id == user.id
        )
    )
    users = result.scalars().all()
    return [
        UserProfile(**{c.name: getattr(u, c.name) for c in u.__table__.columns})
        for u in users
    ]


@router.get("/{username}/following", response_model=list[UserProfile])
async def get_following(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    user = await db.scalar(select(User).where(User.username == username.lower()))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(User).join(Follow, Follow.following_id == User.id).where(
            Follow.follower_id == user.id
        )
    )
    users = result.scalars().all()
    return [
        UserProfile(**{c.name: getattr(u, c.name) for c in u.__table__.columns})
        for u in users
    ]
