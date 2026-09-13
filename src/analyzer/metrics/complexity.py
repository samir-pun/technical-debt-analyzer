"""
complexity.py

Cyclomatic complexity, calculated via radon.

We use radon's own letter-grade bands (A-F) rather than inventing our
own numeric cutoffs, since that gives us a defensible, citable basis:

    A: 1-5    simple, low risk
    B: 6-10   still low risk
    C: 11-20  moderate risk
    D: 21-30  more than moderate risk
    E: 31-40  high risk
    F: 41+    very high risk
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from radon.complexity import cc_rank, cc_visit


@dataclass
class FunctionComplexity:
    name: str
    lineno: int
    complexity: int
    rank: str  # 'A' through 'F'


@dataclass
class ComplexityResult:
    functions: List[FunctionComplexity]
    average_complexity: float
    max_complexity: int


def calculate_complexity(source: str) -> ComplexityResult:
    """Run radon's complexity visitor over a source file's text."""
    try:
        blocks = cc_visit(source)
    except SyntaxError:
        return ComplexityResult(functions=[], average_complexity=0.0, max_complexity=0)

    functions = [
        FunctionComplexity(
            name=block.name,
            lineno=block.lineno,
            complexity=block.complexity,
            rank=cc_rank(block.complexity),
        )
        for block in blocks
    ]

    if not functions:
        return ComplexityResult(functions=[], average_complexity=0.0, max_complexity=0)

    complexities = [f.complexity for f in functions]
    return ComplexityResult(
        functions=functions,
        average_complexity=sum(complexities) / len(complexities),
        max_complexity=max(complexities),
    )