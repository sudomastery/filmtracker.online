import uuid
from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, Field


class MovieBase(BaseModel):
    tmdb_id: int
    title: str
    release_year: int | None = None
    release_date: str | None = None
    poster_url: str | None = None
    backdrop_url: str | None = None
    overview: str | None = None
    genres: Any = None
    runtime: int | None = None
    tmdb_rating: float | None = None
    tmdb_vote_count: int | None = None


class MoviePublic(MovieBase):
    id: uuid.UUID
    avg_user_rating: float | None = None
    user_rating_count: int = 0

    model_config = {"from_attributes": True}


class RatingCreate(BaseModel):
    tmdb_id: int
    score: float | None = Field(None, ge=0, le=10)
    review: str | None = Field(None, max_length=2000)
    contains_spoiler: bool = False
    watched_on: date | None = None


class RatingPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    movie_id: uuid.UUID
    score: float | None
    review: str | None
    contains_spoiler: bool
    watched_on: date | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RatingWithUser(RatingPublic):
    user: "UserPublic"
    movie: MoviePublic


from app.schemas.user import UserPublic  # noqa: E402
RatingWithUser.model_rebuild()


class WatchlistCreate(BaseModel):
    tmdb_id: int
    status: str = "want_to_watch"


class WatchlistUpdate(BaseModel):
    status: str


class WatchlistPublic(BaseModel):
    id: uuid.UUID
    movie_id: uuid.UUID
    status: str
    added_at: datetime
    movie: MoviePublic

    model_config = {"from_attributes": True}
