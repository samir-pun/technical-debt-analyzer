"""
loc.py

Lines-of-code metrics: total, code, comment, and blank line counts.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LocResult:
    total_loc: int
    code_loc: int
    comment_loc: int
    blank_loc: int


def calculate_loc(source: str) -> LocResult:
    """Count total/code/comment/blank lines in a source file."""
    lines = source.splitlines()

    total = len(lines)
    blank = 0
    comment = 0
    code = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            blank += 1
        elif line.startswith("#"):
            comment += 1
        else:
            code += 1

    return LocResult(total_loc=total, code_loc=code, comment_loc=comment, blank_loc=blank)
