from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, get_redis
from app.api.dependencies.auth import get_current_user, get_optional_user
from app.models.user import User
from app.services import feed as feed_service
from app.schemas.feed import FeedPage

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/me", response_model=FeedPage)
async def get_my_feed(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await feed_service.get_user_feed(db, current_user.id, cursor, limit)


@router.get("", response_model=FeedPage)
async def get_feed(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await feed_service.get_feed(db, current_user.id, cursor, limit)


@router.get("/global", response_model=FeedPage)
async def get_global_feed(
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await feed_service.get_global_feed(db, cursor, limit)
