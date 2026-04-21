from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


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

    model_config = ConfigDict(populate_by_name=True)

    identifier: str = Field(
        min_length=3,
        max_length=255,
        validation_alias=AliasChoices("identifier", "username", "email"),
        serialization_alias="identifier",
    )
    password: str = Field(min_length=8, max_length=128)


class UserAuthResponse(BaseModel):
    """Schema for successful registration and login responses."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


class TokenPayload(BaseModel):
    """Schema for JWT payload validation in tests and future auth dependencies."""

    sub: str
    username: str
    email: EmailStr
