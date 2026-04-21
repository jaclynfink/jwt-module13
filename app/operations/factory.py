from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeAlias


Number: TypeAlias = int | float


class CalculationStrategy(ABC):
    """Strategy interface for arithmetic operations."""

    @abstractmethod
    def execute(self, a: Number, b: Number) -> float:
        """Run an operation and return the numeric result."""


class AddStrategy(CalculationStrategy):
    def execute(self, a: Number, b: Number) -> float:
        return float(a + b)


class SubtractStrategy(CalculationStrategy):
    def execute(self, a: Number, b: Number) -> float:
        return float(a - b)


class MultiplyStrategy(CalculationStrategy):
    def execute(self, a: Number, b: Number) -> float:
        return float(a * b)


class DivideStrategy(CalculationStrategy):
    def execute(self, a: Number, b: Number) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return float(a / b)


class CalculationFactory:
    """Factory for creating calculation strategies by operation type."""

    _strategy_map = {
        "add": AddStrategy,
        "sub": SubtractStrategy,
        "subtract": SubtractStrategy,
        "multiply": MultiplyStrategy,
        "mul": MultiplyStrategy,
        "divide": DivideStrategy,
        "div": DivideStrategy,
    }

    @classmethod
    def create(cls, operation_type: str) -> CalculationStrategy:
        normalized = operation_type.strip().lower()
        strategy_cls = cls._strategy_map.get(normalized)
        if strategy_cls is None:
            raise ValueError(f"Unsupported calculation type: {operation_type}")
        return strategy_cls()

    @classmethod
    def calculate(cls, operation_type: str, a: Number, b: Number) -> float:
        return cls.create(operation_type).execute(a, b)
