"""A small, clean calculator module."""

from __future__ import annotations


def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


def subtract(a: float, b: float) -> float:
    """Return the difference of two numbers."""
    return a - b


class Calculator:
    """A tiny calculator that keeps a running total."""

    def __init__(self) -> None:
        self.total = 0.0

    def apply(self, operation: str, value: float) -> float:
        """Apply an operation to the running total."""
        if operation == "add":
            self.total = add(self.total, value)
        elif operation == "subtract":
            self.total = subtract(self.total, value)
        return self.total