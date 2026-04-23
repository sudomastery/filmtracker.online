# Import all models here so Alembic can discover them
from app.models.user import User
from app.models.follow import Follow
from app.models.movie import Movie
from app.models.rating import Rating
from app.models.rating_like import RatingLike
from app.models.watchlist import Watchlist
from app.models.genre_preference import UserGenrePreference
from app.models.notification import Notification

__all__ = [
    "User",
    "Follow",
    "Movie",
    "Rating",
    "RatingLike",
    "Watchlist",
    "UserGenrePreference",
    "Notification",
]
