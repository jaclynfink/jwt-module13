A FastAPI project with a SQLAlchemy `User` model, Pydantic schemas, password hashing, unit/integration tests, and CI/CD to Docker Hub.

## Features

- **FastAPI** REST API
- **SQLAlchemy** ORM user model
  - `username`
  - `email`
  - `password_hash`
  - `created_at`
- **Pydantic** schemas
  - `UserCreate` for input validation
  - `UserRead` for safe API responses
- **Password security**
  - Passlib `CryptContext`
  - `bcrypt_sha256` hashing + verification helpers
- **Testing**
  - Unit tests (hashing, schema validation, etc.)
  - Integration tests with real Postgres
- **CI/CD (GitHub Actions)**
  - Run tests
  - Container security scan (Trivy)
  - Build and push image to Docker Hub

---

## Local Setup

### 1) Clone and enter project

```bash
git clone <your-repo-url>
cd sqlalchemy-module10
```

### 2) Create and activate virtual environment (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment

Create `.env` (or export directly in shell) with your DB connection:

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/myappdb"
```

### 5) Run the app

```bash
uvicorn main:app --reload
```

Open:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

---

## Running Tests

### Unit tests

```bash
pytest -q tests/unit
```

### New calculation unit tests

Run only the new calculation-focused unit tests (factory, schema validation, and model behavior):

```bash
pytest -q tests/unit/test_calculation_factory.py tests/unit/test_calculation_model.py tests/unit/test_calculation_schemas.py
```

### Integration tests (requires Postgres)

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/myappdb"
pytest -q tests/integration
```

### API integration tests (Postgres-backed endpoint tests)

These tests hit the FastAPI endpoints through TestClient while using a real Postgres session.

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/myappdb"
pytest -q tests/integration/test_api_endpoints_postgres_integration.py
```

What this verifies:

- User register and login endpoint flow
- Password is hashed and stored in DB (not plain text)
- Calculation BREAD flow:
  - Add (POST /calculations)
  - Browse (GET /calculations)
  - Read (GET /calculations/{id})
  - Edit (PUT /calculations/{id})
  - Delete (DELETE /calculations/{id})
- Invalid payloads return expected error status codes and error JSON fields

### Run integration tests in CI-style mode locally

If you want local behavior similar to GitHub Actions:

```bash
docker run --name local-pg -e POSTGRES_USER=user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=myappdb -p 5432:5432 -d postgres:latest
export DATABASE_URL="postgresql://user:password@localhost:5432/myappdb"
pytest -q tests/integration
docker rm -f local-pg
```

### New calculation integration tests (requires Postgres)

```bash
export DATABASE_URL="postgresql+psycopg2://user:password@localhost:5432/myappdb"
pytest -q tests/integration/test_calculation_integration.py
```

### Full test suite

```bash
pytest -q
```

---

## Manual Checks via OpenAPI

### 1) Start the API

```bash
uvicorn main:app --reload
```

### 2) Open API docs

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### 3) Manually test User endpoints in Swagger UI

1. Expand POST /users/register and click Try it out.
2. Use payload example:

  {
    "username": "manual_user",
    "email": "manual_user@example.com",
    "password": "StrongPass123"
  }

3. Confirm response code is 201 and response includes id, username, email, created_at.
4. Expand POST /users/login and click Try it out.
5. Use payload example:

  {
    "username": "manual_user",
    "password": "StrongPass123"
  }

6. Confirm response code is 200 and response contains message plus user object.

### 4) Manually test Calculation BREAD endpoints in Swagger UI

1. POST /calculations

  {
    "a": 10,
    "b": 5,
    "type": "Add"
  }

  Confirm 201 and copy returned id.

2. GET /calculations
  Confirm the new record appears.

3. GET /calculations/{id}
  Use the copied id and confirm 200.

4. PUT /calculations/{id}

  {
    "a": 9,
    "b": 3,
    "type": "Multiply"
  }

  Confirm 200 and updated result.

5. DELETE /calculations/{id}
  Confirm 204.

6. GET /calculations/{id} again
  Confirm 404 with Calculation not found error.

### 5) Manual negative tests

- POST /calculations with invalid type (for example type: "Power") should return 400.
- POST /calculations with Divide and b=0 should return 400.
- POST /users/login with wrong password should return 401.

---

## Docker

### Build image

```bash
docker build -t sqlalchemy-module10:local .
```

### Run with local Postgres container

```bash
docker network create appnet

docker run -d \
  --name mypg \
  --network appnet \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=myappdb \
  -p 5432:5432 \
  postgres:latest

docker run --rm -it \
  --name myapp \
  --network appnet \
  -e DATABASE_URL="postgresql+psycopg2://user:password@mypg:5432/myappdb" \
  -p 8000:8000 \
  sqlalchemy-module10:local
```

---

## CI/CD Pipeline

Workflow: `.github/workflows/test.yml`

On push/PR to `main`, pipeline runs:

1. **test**: unit + integration tests  
2. **security**: Trivy image scan  
3. **deploy** (main only): push image to Docker Hub

### Required GitHub Secrets

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN` (must include **read + write** scopes)