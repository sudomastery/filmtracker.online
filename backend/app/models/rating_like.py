from sqlalchemy import Column, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class RatingLike(Base):
    __tablename__ = "rating_likes"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    rating_id = Column(
        UUID(as_uuid=True),
        ForeignKey("ratings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
