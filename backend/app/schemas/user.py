import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    display_name: str | None = Field(None, max_length=60)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username may only contain letters, numbers and underscores")
        return v.lower()


class UserLogin(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str | None
    avatar_url: str | None
    bio: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMe(UserPublic):
    email: str
    onboarding_complete: bool
    follower_count: int = 0
    following_count: int = 0

    model_config = {"from_attributes": True}


class UserProfile(UserPublic):
    follower_count: int = 0
    following_count: int = 0
    rating_count: int = 0
    is_following: bool = False

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=60)
    bio: str | None = Field(None, max_length=300)
    avatar_url: str | None = None
