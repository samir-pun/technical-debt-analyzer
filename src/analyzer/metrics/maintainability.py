"""
maintainability.py

Maintainability Index, via radon. A single 0-100 score combining
Halstead Volume, Cyclomatic Complexity, and LOC — higher is better.
"""

from __future__ import annotations

from dataclasses import dataclass

from radon.metrics import mi_rank, mi_visit


@dataclass
class MaintainabilityResult:
    score: float   # 0-100, higher = more maintainable
    rank: str      # 'A' (best) - 'C' (worst), radon's own banding


def calculate_maintainability(source: str) -> MaintainabilityResult:
    """Run radon's Maintainability Index calculation on source text."""
    try:
        score = mi_visit(source, multi=True)
    except SyntaxError:
        return MaintainabilityResult(score=0.0, rank="C")

    return MaintainabilityResult(score=score, rank=mi_rank(score))