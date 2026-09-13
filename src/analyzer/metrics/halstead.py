"""
halstead.py

Halstead metrics, via radon.

Derived from counts of operators and operands in the source:
    n1 = distinct operators       n2 = distinct operands
    N1 = total operators          N2 = total operands

    vocabulary = n1 + n2
    length     = N1 + N2
    volume     = length * log2(vocabulary)
    difficulty = (n1 / 2) * (N2 / n2)
    effort     = difficulty * volume
"""

from __future__ import annotations

from dataclasses import dataclass

from radon.metrics import h_visit


@dataclass
class HalsteadResult:
    vocabulary: float
    length: float
    volume: float
    difficulty: float
    effort: float


def calculate_halstead(source: str) -> HalsteadResult:
    """Run radon's Halstead visitor and return file-level totals."""
    try:
        report = h_visit(source)
    except SyntaxError:
        return HalsteadResult(vocabulary=0, length=0, volume=0, difficulty=0, effort=0)

    total = report.total  # radon's aggregate for the whole file
    return HalsteadResult(
        vocabulary=total.vocabulary,
        length=total.length,
        volume=total.volume,
        difficulty=total.difficulty,
        effort=total.effort,
    )