from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password before storing it."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    return pwd_context.verify(plain_password, password_hash)
