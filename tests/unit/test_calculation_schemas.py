import pytest
from pydantic import ValidationError

from app.schemas.calculation import CalculationCreate, CalculationRead, CalculationType


class _CalculationRecord:
    def __init__(self) -> None:
        self.id = 1
        self.a = 10.0
        self.b = 5.0
        self.type = CalculationType.ADD
        self.result = 15.0
        self.user_id = 2


def test_calculation_create_accepts_valid_payload() -> None:
    payload = CalculationCreate(a=10, b=5, type=CalculationType.ADD, result=15, user_id=1)

    assert payload.a == 10
    assert payload.b == 5
    assert payload.result == 15


def test_calculation_create_rejects_division_by_zero() -> None:
    with pytest.raises(ValidationError):
        CalculationCreate(a=10, b=0, type=CalculationType.DIVIDE)


def test_calculation_create_rejects_result_mismatch() -> None:
    with pytest.raises(ValidationError):
        CalculationCreate(a=10, b=5, type=CalculationType.MULTIPLY, result=10)


def test_calculation_create_rejects_non_finite_operands() -> None:
    with pytest.raises(ValidationError):
        CalculationCreate(a=float("inf"), b=5, type=CalculationType.ADD)


def test_calculation_create_accepts_case_insensitive_type_string() -> None:
    payload = CalculationCreate(a=9, b=3, type="divide")

    assert payload.type == CalculationType.DIVIDE


def test_calculation_create_rejects_invalid_type_string() -> None:
    with pytest.raises(ValidationError):
        CalculationCreate(a=9, b=3, type="modulo")


def test_calculation_create_rejects_non_positive_user_id() -> None:
    with pytest.raises(ValidationError):
        CalculationCreate(a=9, b=3, type="add", user_id=0)


def test_calculation_read_supports_orm_model_validation() -> None:
    record = _CalculationRecord()

    serialized = CalculationRead.model_validate(record).model_dump()

    assert serialized["id"] == 1
    assert serialized["type"] == CalculationType.ADD
    assert serialized["result"] == 15
    assert serialized["user_id"] == 2
