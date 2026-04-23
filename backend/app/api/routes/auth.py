from fastapi import APIRouter, Depends, HTTPException, status, Response, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db, get_redis
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserRegister
from app.schemas.auth import TokenPair, RefreshRequest, AccessToken

router = APIRouter(prefix="/auth", tags=["auth"])


async def _issue_tokens(user_id: str, redis) -> TokenPair:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    await redis.setex(
        f"refresh:{refresh_token}",
        settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        user_id,
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(
        select(User).where(
            (User.username == payload.username) | (User.email == payload.email)
        )
    )
    if existing:
        field = "username" if existing.username == payload.username else "email"
        raise HTTPException(status_code=400, detail=f"{field} already taken")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name or payload.username,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    redis = await get_redis()
    return await _issue_tokens(str(user.id), redis)


@router.post("/login", response_model=TokenPair)
async def login(
    username: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    # Try username first, then email
    user = await db.scalar(select(User).where(User.username == username.lower()))
    if not user:
        user = await db.scalar(select(User).where(User.email == username))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    redis = await get_redis()
    return await _issue_tokens(str(user.id), redis)


@router.post("/refresh", response_model=AccessToken)
async def refresh_token(payload: RefreshRequest):
    token_data = decode_token(payload.refresh_token)
    if not token_data or token_data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    redis = await get_redis()
    stored = await redis.get(f"refresh:{payload.refresh_token}")
    if not stored:
        raise HTTPException(status_code=401, detail="Refresh token expired or revoked")

    access_token = create_access_token(stored)
    return AccessToken(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest):
    redis = await get_redis()
    await redis.delete(f"refresh:{payload.refresh_token}")
    return Response(status_code=204)
