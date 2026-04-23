from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.models.genre_preference import UserGenrePreference
from app.services.recommendations import get_suggested_users

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/genres")
async def save_genres(
    genre_ids: list[int] = Body(...),
    genre_names: list[str] = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Clear existing preferences
    await db.execute(
        delete(UserGenrePreference).where(UserGenrePreference.user_id == current_user.id)
    )
    for gid, gname in zip(genre_ids, genre_names):
        db.add(UserGenrePreference(
            user_id=current_user.id,
            genre_id=gid,
            genre_name=gname,
        ))
    await db.flush()
    return {"detail": "Genres saved", "count": len(genre_ids)}


@router.get("/suggestions")
async def get_suggestions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get user's saved genre preferences
    result = await db.execute(
        select(UserGenrePreference).where(UserGenrePreference.user_id == current_user.id)
    )
    prefs = result.scalars().all()
    genre_ids = [p.genre_id for p in prefs]

    suggestions = await get_suggested_users(db, current_user.id, genre_ids)
    return suggestions


@router.post("/complete")
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.onboarding_complete = True
    await db.flush()
    return {"detail": "Onboarding complete"}
