import uuid
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserGenrePreference(Base):
    __tablename__ = "user_genre_preferences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    genre_id: Mapped[int] = mapped_column(Integer, nullable=False)
    genre_name: Mapped[str] = mapped_column(nullable=False)
