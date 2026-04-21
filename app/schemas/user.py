from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for incoming user registration payloads."""

    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    """Schema for API responses that expose safe user fields only."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class UserLogin(BaseModel):
    """Schema for incoming login payloads."""

    username: str = Field(min_length=4, max_length=40)
    password: str = Field(min_length=8, max_length=128)


class UserLoginResponse(BaseModel):
    """Schema for successful login responses."""

    message: str
    user: UserRead
