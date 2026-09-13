"""
long_function.py

Detects functions/methods that are too long.
"""

from __future__ import annotations

import ast
from typing import List

from .models import Smell

MEDIUM_THRESHOLD = 40   # lines
HIGH_THRESHOLD = 70     # lines


def _severity_for_length(length: int) -> str:
    if length >= HIGH_THRESHOLD:
        return "High"
    if length >= MEDIUM_THRESHOLD:
        return "Medium"
    return "Low"


def detect_long_functions(tree: ast.AST, relative_path: str) -> List[Smell]:
    """Walk the AST and flag any function above MEDIUM_THRESHOLD lines."""
    smells: List[Smell] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        end_lineno = getattr(node, "end_lineno", None)
        if end_lineno is None:
            continue

        length = end_lineno - node.lineno + 1
        if length < MEDIUM_THRESHOLD:
            continue

        smells.append(
            Smell(
                file=relative_path,
                line=node.lineno,
                type="Long Function",
                severity=_severity_for_length(length),
                explanation=f"Function '{node.name}' contains {length} lines.",
            )
        )

    return smells