"""
naming.py

Detects naming that doesn't follow PEP 8 conventions.
"""

from __future__ import annotations

import ast
import re
from typing import List

from .models import Smell

SNAKE_CASE_RE = re.compile(r"^_{0,2}[a-z][a-z0-9_]*$")
PASCAL_CASE_RE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
ALLOWED_SHORT_NAMES = {"i", "j", "k", "x", "y", "z", "_", "df", "fn", "ax"}


def _is_bad_function_name(name: str) -> bool:
    if name.startswith("__") and name.endswith("__"):
        return False  # dunder methods like __init__
    if len(name) <= 1 and name not in ALLOWED_SHORT_NAMES:
        return True
    return not SNAKE_CASE_RE.match(name)


def _is_bad_class_name(name: str) -> bool:
    return not PASCAL_CASE_RE.match(name)


def detect_naming_issues(tree: ast.AST, relative_path: str) -> List[Smell]:
    smells: List[Smell] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _is_bad_function_name(node.name):
                smells.append(
                    Smell(
                        file=relative_path,
                        line=node.lineno,
                        type="Poor Naming",
                        severity="Low",
                        explanation=f"Function name '{node.name}' does not follow snake_case convention.",
                    )
                )
        elif isinstance(node, ast.ClassDef):
            if _is_bad_class_name(node.name):
                smells.append(
                    Smell(
                        file=relative_path,
                        line=node.lineno,
                        type="Poor Naming",
                        severity="Low",
                        explanation=f"Class name '{node.name}' does not follow PascalCase convention.",
                    )
                )

    return smells