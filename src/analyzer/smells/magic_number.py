"""
magic_number.py

Detects numeric literals used directly in code instead of being
assigned to a named constant.
"""

from __future__ import annotations

import ast
from typing import List

from .models import Smell

ALLOWED_NUMBERS = {0, 1, -1, 2, 100}


def detect_magic_numbers(tree: ast.AST, relative_path: str) -> List[Smell]:
    smells: List[Smell] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if not isinstance(node.value, (int, float)) or isinstance(node.value, bool):
            continue
        if node.value in ALLOWED_NUMBERS:
            continue

        smells.append(
            Smell(
                file=relative_path,
                line=getattr(node, "lineno", 0),
                type="Magic Number",
                severity="Low",
                explanation=f"Literal value {node.value!r} used directly instead of a named constant.",
            )
        )

    return smells