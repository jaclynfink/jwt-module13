import pytest

from app.operations.factory import (
    AddStrategy,
    CalculationFactory,
    DivideStrategy,
    MultiplyStrategy,
    SubtractStrategy,
)


@pytest.mark.parametrize(
    "operation,expected_type",
    [
        ("add", AddStrategy),
        ("Add", AddStrategy),
        ("sub", SubtractStrategy),
        ("Sub", SubtractStrategy),
        ("subtract", SubtractStrategy),
        ("multiply", MultiplyStrategy),
        ("Multiply", MultiplyStrategy),
        ("mul", MultiplyStrategy),
        ("divide", DivideStrategy),
        ("Divide", DivideStrategy),
        ("div", DivideStrategy),
    ],
)
def test_factory_creates_expected_strategy(operation: str, expected_type: type) -> None:
    strategy = CalculationFactory.create(operation)

    assert isinstance(strategy, expected_type)


@pytest.mark.parametrize(
    "operation,a,b,expected",
    [
        ("add", 10, 5, 15.0),
        ("subtract", 10, 5, 5.0),
        ("multiply", 10, 5, 50.0),
        ("divide", 10, 5, 2.0),
    ],
)
def test_factory_calculate_returns_expected_result(
    operation: str,
    a: int,
    b: int,
    expected: float,
) -> None:
    assert CalculationFactory.calculate(operation, a, b) == expected


def test_factory_divide_by_zero_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        CalculationFactory.calculate("divide", 10, 0)


def test_factory_rejects_unknown_operation() -> None:
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        CalculationFactory.create("mod")
