from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserRead


class _UserRecord:
    """Simple object used to validate ORM-style schema parsing."""

    def __init__(self) -> None:
        self.id = 1
        self.username = "schema_user"
        self.email = "schema@example.com"
        self.password_hash = "$2b$12$hashvalue"
        self.created_at = datetime.now(timezone.utc)


def test_user_create_accepts_valid_payload() -> None:
    payload = UserCreate(username="newuser", email="newuser@example.com", password="StrongPass123")

    assert payload.username == "newuser"
    assert payload.email == "newuser@example.com"


def test_user_create_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="newuser", email="invalid-email", password="StrongPass123")


def test_user_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="newuser", email="newuser@example.com", password="short")


def test_user_read_omits_password_hash() -> None:
    record = _UserRecord()

    serialized = UserRead.model_validate(record).model_dump()

    assert serialized["username"] == "schema_user"
    assert "password_hash" not in serialized
