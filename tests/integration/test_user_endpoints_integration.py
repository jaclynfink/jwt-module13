import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models.user import User
from main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.mark.integration
def test_register_user_success(client):
    response = client.post(
        "/users/register",
        json={
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "StrongPass123",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["username"] == "new_user"
    assert payload["email"] == "new_user@example.com"
    assert "created_at" in payload
    assert "password" not in payload
    assert "password_hash" not in payload


@pytest.mark.integration
def test_register_user_duplicate_username(client):
    first = {
        "username": "duplicate_user",
        "email": "first@example.com",
        "password": "StrongPass123",
    }
    second = {
        "username": "duplicate_user",
        "email": "second@example.com",
        "password": "StrongPass123",
    }

    assert client.post("/users/register", json=first).status_code == 201
    response = client.post("/users/register", json=second)

    assert response.status_code == 409
    assert response.json()["error"] == "Username already exists."


@pytest.mark.integration
def test_register_user_duplicate_email(client):
    first = {
        "username": "first_user",
        "email": "duplicate@example.com",
        "password": "StrongPass123",
    }
    second = {
        "username": "second_user",
        "email": "duplicate@example.com",
        "password": "StrongPass123",
    }

    assert client.post("/users/register", json=first).status_code == 201
    response = client.post("/users/register", json=second)

    assert response.status_code == 409
    assert response.json()["error"] == "Email already exists."


@pytest.mark.integration
def test_login_user_success(client):
    register_payload = {
        "username": "login_user",
        "email": "login_user@example.com",
        "password": "StrongPass123",
    }
    client.post("/users/register", json=register_payload)

    response = client.post(
        "/users/login",
        json={"username": "login_user", "password": "StrongPass123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Login successful."
    assert payload["user"]["username"] == "login_user"


@pytest.mark.integration
def test_login_user_wrong_password(client):
    register_payload = {
        "username": "wrong_password_user",
        "email": "wrong_password_user@example.com",
        "password": "StrongPass123",
    }
    client.post("/users/register", json=register_payload)

    response = client.post(
        "/users/login",
        json={"username": "wrong_password_user", "password": "WrongPassword"},
    )

    assert response.status_code == 401
    assert response.json()["error"] == "Invalid username or password."


@pytest.mark.integration
def test_register_stores_password_hash(client):
    response = client.post(
        "/users/register",
        json={
            "username": "hash_check_user",
            "email": "hash_check_user@example.com",
            "password": "StrongPass123",
        },
    )

    user_id = response.json()["id"]

    session_gen = app.dependency_overrides[get_db]()
    db = next(session_gen)
    try:
        user = db.get(User, user_id)
    finally:
        db.close()

    assert user is not None
    assert user.password_hash != "StrongPass123"


@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "ab",  # min_length is 3
            "email": "too_short_username@example.com",
            "password": "StrongPass123",
        },
        {
            "username": "u" * 51,  # max_length is 50
            "email": "too_long_username@example.com",
            "password": "StrongPass123",
        },
        {
            "username": "valid_name",
            "email": "short_password@example.com",
            "password": "short",  # min_length is 8
        },
        {
            "username": "valid_name_2",
            "email": "long_password@example.com",
            "password": "p" * 129,  # max_length is 128
        },
    ],
)
def test_register_rejects_username_or_password_out_of_bounds(client, payload):
    response = client.post("/users/register", json=payload)

    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.integration
@pytest.mark.parametrize(
    "payload",
    [
        {"username": "abc", "password": "StrongPass123"},  # login username min_length is 4
        {"username": "u" * 41, "password": "StrongPass123"},  # login username max_length is 40
        {"username": "validlogin", "password": "short"},  # login password min_length is 8
        {"username": "validlogin", "password": "p" * 129},  # login password max_length is 128
    ],
)
def test_login_rejects_username_or_password_out_of_bounds(client, payload):
    response = client.post("/users/login", json=payload)

    assert response.status_code == 400
    assert "error" in response.json()
