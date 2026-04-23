import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, SmallInteger, Numeric, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    original_title: Mapped[str | None] = mapped_column(String(255))
    release_year: Mapped[int | None] = mapped_column(SmallInteger)
    release_date: Mapped[str | None] = mapped_column(String(10))
    poster_url: Mapped[str | None] = mapped_column(Text)
    backdrop_url: Mapped[str | None] = mapped_column(Text)
    overview: Mapped[str | None] = mapped_column(Text)
    genres: Mapped[dict | None] = mapped_column(JSONB)
    runtime: Mapped[int | None] = mapped_column(SmallInteger)
    tmdb_rating: Mapped[float | None] = mapped_column(Numeric(3, 1))
    tmdb_vote_count: Mapped[int | None] = mapped_column(Integer)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
