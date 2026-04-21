import os

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models.user import User
from app.schemas.user import UserCreate
from app.security import hash_password


@pytest.fixture(scope="session")
def postgres_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not set. Skipping Postgres integration tests.")

    return database_url


@pytest.fixture(scope="session")
def engine(postgres_url: str):
    db_engine = create_engine(postgres_url, future=True)
    Base.metadata.create_all(bind=db_engine)
    yield db_engine
    Base.metadata.drop_all(bind=db_engine)
    db_engine.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    connection = engine.connect()
    transaction = connection.begin()
    testing_session = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)()

    try:
        yield testing_session
    finally:
        testing_session.close()
        transaction.rollback()
        connection.close()


@pytest.mark.integration
def test_user_username_must_be_unique(db_session: Session) -> None:
    first_user = User(
        username="duplicate_name",
        email="first@example.com",
        password_hash=hash_password("StrongPass123"),
    )
    db_session.add(first_user)
    db_session.commit()

    duplicate_username_user = User(
        username="duplicate_name",
        email="second@example.com",
        password_hash=hash_password("StrongPass123"),
    )
    db_session.add(duplicate_username_user)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.integration
def test_user_email_must_be_unique(db_session: Session) -> None:
    first_user = User(
        username="first_name",
        email="same@example.com",
        password_hash=hash_password("StrongPass123"),
    )
    db_session.add(first_user)
    db_session.commit()

    duplicate_email_user = User(
        username="second_name",
        email="same@example.com",
        password_hash=hash_password("StrongPass123"),
    )
    db_session.add(duplicate_email_user)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.integration
def test_user_created_at_is_set_by_database(db_session: Session) -> None:
    user = User(
        username="timestamp_user",
        email="timestamp@example.com",
        password_hash=hash_password("StrongPass123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.created_at is not None


@pytest.mark.integration
def test_invalid_email_is_rejected_before_insert() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="bademail", email="not-an-email", password="StrongPass123")
