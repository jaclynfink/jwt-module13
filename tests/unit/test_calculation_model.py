import pytest

from app.models.calculation import Calculation, CalculationType


def test_calculation_model_has_expected_columns() -> None:
    columns = Calculation.__table__.columns

    assert "id" in columns
    assert "a" in columns
    assert "b" in columns
    assert "type" in columns
    assert "result" in columns
    assert "user_id" in columns


def test_calculation_model_user_id_has_foreign_key_to_users() -> None:
    user_id_column = Calculation.__table__.columns["user_id"]

    assert len(user_id_column.foreign_keys) == 1
    foreign_key = next(iter(user_id_column.foreign_keys))
    assert foreign_key.target_fullname == "users.id"


def test_calculation_model_computed_result_for_supported_operations() -> None:
    add_calc = Calculation(a=10, b=5, type=CalculationType.ADD.value)
    subtract_calc = Calculation(a=10, b=5, type=CalculationType.SUB.value)
    multiply_calc = Calculation(a=10, b=5, type=CalculationType.MULTIPLY.value)
    divide_calc = Calculation(a=10, b=5, type=CalculationType.DIVIDE.value)

    assert add_calc.computed_result == 15
    assert subtract_calc.computed_result == 5
    assert multiply_calc.computed_result == 50
    assert divide_calc.computed_result == 2


def test_calculation_model_resolved_result_prefers_stored_result() -> None:
    calc = Calculation(a=10, b=5, type=CalculationType.ADD.value, result=999)

    assert calc.resolved_result == 999


def test_calculation_model_computed_result_rejects_divide_by_zero() -> None:
    calc = Calculation(a=10, b=0, type=CalculationType.DIVIDE.value)

    with pytest.raises(ValueError, match="divide by zero"):
        _ = calc.computed_result
