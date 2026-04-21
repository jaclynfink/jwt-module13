import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.models.calculation import Calculation
from app.models.user import User
from app.security import verify_password
from main import app


@pytest.fixture(scope="session")
def postgres_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is not set. Skipping Postgres API integration tests.")
    return database_url


@pytest.fixture(scope="session")
def api_engine(postgres_url: str):
    engine = create_engine(postgres_url, future=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def api_db_session(api_engine) -> Generator[Session, None, None]:
    connection = api_engine.connect()
    transaction = connection.begin()
    testing_session = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)()

    try:
        yield testing_session
    finally:
        testing_session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def api_client(api_db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield api_db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.integration
def test_user_register_login_and_data_persisted_in_db(api_client: TestClient, api_db_session: Session) -> None:
    register_payload = {
        "username": "pg_api_user",
        "email": "pg_api_user@example.com",
        "password": "StrongPass123",
    }

    register_response = api_client.post("/users/register", json=register_payload)
    assert register_response.status_code == 201
    registered = register_response.json()
    assert registered["username"] == register_payload["username"]
    assert registered["email"] == register_payload["email"]

    persisted_user = (
        api_db_session.query(User)
        .filter(User.username == register_payload["username"])
        .first()
    )
    assert persisted_user is not None
    assert persisted_user.password_hash != register_payload["password"]
    assert verify_password(register_payload["password"], persisted_user.password_hash) is True

    login_response = api_client.post(
        "/users/login",
        json={"username": register_payload["username"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["username"] == register_payload["username"]


@pytest.mark.integration
def test_calculation_bread_create_read_update_delete(api_client: TestClient, api_db_session: Session) -> None:
    create_response = api_client.post(
        "/calculations",
        json={"a": 10, "b": 5, "type": "Add"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    calc_id = created["id"]
    assert created["result"] == 15

    persisted = api_db_session.get(Calculation, calc_id)
    assert persisted is not None
    assert persisted.result == 15

    browse_response = api_client.get("/calculations")
    assert browse_response.status_code == 200
    assert any(item["id"] == calc_id for item in browse_response.json())

    read_response = api_client.get(f"/calculations/{calc_id}")
    assert read_response.status_code == 200
    assert read_response.json()["id"] == calc_id

    update_response = api_client.put(
        f"/calculations/{calc_id}",
        json={"a": 9, "b": 3, "type": "Multiply"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["result"] == 27

    delete_response = api_client.delete(f"/calculations/{calc_id}")
    assert delete_response.status_code == 204

    read_after_delete = api_client.get(f"/calculations/{calc_id}")
    assert read_after_delete.status_code == 404
    assert read_after_delete.json()["error"] == "Calculation not found."


@pytest.mark.integration
def test_calculation_invalid_payload_returns_error_response(api_client: TestClient) -> None:
    invalid_type_response = api_client.post(
        "/calculations",
        json={"a": 10, "b": 2, "type": "Power"},
    )
    assert invalid_type_response.status_code == 400
    assert "error" in invalid_type_response.json()

    divide_by_zero_response = api_client.post(
        "/calculations",
        json={"a": 10, "b": 0, "type": "Divide"},
    )
    assert divide_by_zero_response.status_code == 400
    assert "error" in divide_by_zero_response.json()

    not_found_update_response = api_client.put(
        "/calculations/999999",
        json={"a": 1, "b": 1, "type": "Add"},
    )
    assert not_found_update_response.status_code == 404
    assert not_found_update_response.json()["error"] == "Calculation not found."

    invalid_path_response = api_client.get("/calculations/not-an-int")
    assert invalid_path_response.status_code == 400
    assert "error" in invalid_path_response.json()
