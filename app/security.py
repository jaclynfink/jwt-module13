import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


def hash_password(password: str) -> str:
    """Hash a plain-text password before storing it."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str, additional_claims: dict[str, Any] | None = None) -> str:
    """Create a signed JWT access token for the authenticated user."""
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": expires_at}
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT access token."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
