from sqlalchemy.sql.functions import now

from app.models.user import User


def test_user_model_has_expected_columns() -> None:
    """User model includes secure credential and timestamp columns."""
    columns = User.__table__.columns

    assert "username" in columns
    assert "email" in columns
    assert "password_hash" in columns
    assert "created_at" in columns


def test_user_model_has_unique_constraints_on_username_and_email() -> None:
    """Username and email columns are individually unique."""
    username_column = User.__table__.columns["username"]
    email_column = User.__table__.columns["email"]

    assert username_column.unique is True
    assert email_column.unique is True


def test_user_model_created_at_server_default_is_now() -> None:
    """created_at defaults to database current timestamp."""
    created_at_column = User.__table__.columns["created_at"]

    assert created_at_column.server_default is not None
    assert isinstance(created_at_column.server_default.arg, now)
