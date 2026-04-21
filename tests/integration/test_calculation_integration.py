import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models.calculation import Calculation, CalculationType
from app.models.user import User
from app.security import hash_password


@pytest.fixture(scope="session")
def calc_postgres_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not set. Skipping Postgres integration tests.")

    return database_url


@pytest.fixture(scope="session")
def calc_engine(calc_postgres_url: str):
    db_engine = create_engine(calc_postgres_url, future=True)
    Base.metadata.create_all(bind=db_engine)
    yield db_engine
    Base.metadata.drop_all(bind=db_engine)
    db_engine.dispose()


@pytest.fixture()
def calc_db_session(calc_engine) -> Session:
    connection = calc_engine.connect()
    transaction = connection.begin()
    testing_session = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)()

    try:
        yield testing_session
    finally:
        testing_session.close()
        transaction.rollback()
        connection.close()


@pytest.mark.integration
def test_insert_calculation_record_persists_expected_data(calc_db_session: Session) -> None:
    record = Calculation(
        a=12,
        b=3,
        type=CalculationType.MULTIPLY.value,
        result=36,
    )

    calc_db_session.add(record)
    calc_db_session.commit()
    calc_db_session.refresh(record)

    assert record.id is not None
    assert record.a == 12
    assert record.b == 3
    assert record.type == CalculationType.MULTIPLY.value
    assert record.result == 36


@pytest.mark.integration
def test_calculation_invalid_type_is_rejected_by_database_constraint(calc_db_session: Session) -> None:
    invalid_record = Calculation(a=10, b=2, type="Power", result=100)
    calc_db_session.add(invalid_record)

    with pytest.raises(IntegrityError):
        calc_db_session.commit()


@pytest.mark.integration
def test_divide_by_zero_is_rejected_by_database_constraint(calc_db_session: Session) -> None:
    invalid_record = Calculation(a=10, b=0, type=CalculationType.DIVIDE.value)
    calc_db_session.add(invalid_record)

    with pytest.raises(IntegrityError):
        calc_db_session.commit()


@pytest.mark.integration
def test_calculation_invalid_user_id_is_rejected_by_foreign_key(calc_db_session: Session) -> None:
    invalid_fk_record = Calculation(
        a=10,
        b=5,
        type=CalculationType.ADD.value,
        result=15,
        user_id=999_999,
    )
    calc_db_session.add(invalid_fk_record)

    with pytest.raises(IntegrityError):
        calc_db_session.commit()


@pytest.mark.integration
def test_calculation_with_valid_user_id_is_persisted(calc_db_session: Session) -> None:
    user = User(
        username="calc_owner",
        email="calc_owner@example.com",
        password_hash=hash_password("StrongPass123"),
    )
    calc_db_session.add(user)
    calc_db_session.commit()
    calc_db_session.refresh(user)

    record = Calculation(
        a=9,
        b=3,
        type=CalculationType.DIVIDE.value,
        user_id=user.id,
    )
    calc_db_session.add(record)
    calc_db_session.commit()
    calc_db_session.refresh(record)

    assert record.user_id == user.id
    assert record.resolved_result == 3
