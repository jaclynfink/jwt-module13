import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
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
def test_add_and_browse_calculations(client):
    create_response = client.post(
        "/calculations",
        json={"a": 10, "b": 2, "type": "Divide"},
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["a"] == 10
    assert created["b"] == 2
    assert created["type"] == "Divide"
    assert created["result"] == 5

    browse_response = client.get("/calculations")
    assert browse_response.status_code == 200
    items = browse_response.json()
    assert len(items) == 1
    assert items[0]["id"] == created["id"]


@pytest.mark.integration
def test_read_calculation_by_id(client):
    create_response = client.post(
        "/calculations",
        json={"a": 7, "b": 8, "type": "Add"},
    )
    calculation_id = create_response.json()["id"]

    read_response = client.get(f"/calculations/{calculation_id}")

    assert read_response.status_code == 200
    payload = read_response.json()
    assert payload["id"] == calculation_id
    assert payload["result"] == 15


@pytest.mark.integration
def test_edit_calculation_with_put(client):
    create_response = client.post(
        "/calculations",
        json={"a": 9, "b": 3, "type": "Sub"},
    )
    calculation_id = create_response.json()["id"]

    update_response = client.put(
        f"/calculations/{calculation_id}",
        json={"a": 9, "b": 3, "type": "Multiply"},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id"] == calculation_id
    assert updated["type"] == "Multiply"
    assert updated["result"] == 27


@pytest.mark.integration
def test_delete_calculation(client):
    create_response = client.post(
        "/calculations",
        json={"a": 20, "b": 5, "type": "Divide"},
    )
    calculation_id = create_response.json()["id"]

    delete_response = client.delete(f"/calculations/{calculation_id}")
    assert delete_response.status_code == 204

    read_response = client.get(f"/calculations/{calculation_id}")
    assert read_response.status_code == 404
    assert read_response.json()["error"] == "Calculation not found."
