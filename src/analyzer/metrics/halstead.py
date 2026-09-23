"""
halstead.py

Halstead metrics, via radon — exposing the FULL set of fields to match
the Sandouka & Aljamaan Python Code Smell Dataset's feature columns.

Known limitation (documented in Week 1 report): radon's Halstead visitor
returns all-zero values for functions containing try/except blocks.
"""

from __future__ import annotations

from dataclasses import dataclass

from radon.metrics import h_visit


@dataclass
class HalsteadResult:
    h1: float                  # number of distinct operators
    h2: float                  # number of distinct operands
    n1: float                  # total number of operators
    n2: float                  # total number of operands
    vocabulary: float
    length: float
    calculated_length: float
    volume: float
    difficulty: float
    effort: float
    time: float
    bugs: float


def calculate_halstead(source: str) -> HalsteadResult:
    """Run radon's Halstead visitor, exposing all fields for dataset compatibility."""
    try:
        report = h_visit(source)
    except SyntaxError:
        return HalsteadResult(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    total = report.total
    return HalsteadResult(
        h1=total.h1,
        h2=total.h2,
        n1=total.N1,
        n2=total.N2,
        vocabulary=total.vocabulary,
        length=total.length,
        calculated_length=total.calculated_length,
        volume=total.volume,
        difficulty=total.difficulty,
        effort=total.effort,
        time=total.time,
        bugs=total.bugs,
    )