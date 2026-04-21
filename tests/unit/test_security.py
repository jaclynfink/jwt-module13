from app.security import hash_password, verify_password


def test_hash_password_returns_hashed_value() -> None:
    """The generated hash should not equal the original password."""
    raw_password = "MyStrongPass123!"

    password_hash = hash_password(raw_password)

    assert password_hash != raw_password
    assert "bcrypt" in password_hash


def test_verify_password_returns_true_for_valid_password() -> None:
    """Verification should succeed for matching plain-text password."""
    raw_password = "CorrectHorseBatteryStaple!"
    password_hash = hash_password(raw_password)

    assert verify_password(raw_password, password_hash) is True


def test_verify_password_returns_false_for_invalid_password() -> None:
    """Verification should fail for non-matching plain-text password."""
    password_hash = hash_password("CorrectPassword123!")

    assert verify_password("WrongPassword123!", password_hash) is False
