import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.movie import MoviePublic
from app.schemas.user import UserPublic


class FeedItem(BaseModel):
    id: uuid.UUID
    user: UserPublic
    movie: MoviePublic
    score: float | None
    review: str | None
    contains_spoiler: bool
    watched_on: str | None
    created_at: datetime
    like_count: int = 0
    liked_by_me: bool = False

    model_config = {"from_attributes": True}


class FeedPage(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None
    has_more: bool
