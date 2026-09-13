"""
models.py

Shared data structure returned by every smell detector.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Smell:
    file: str          # relative path of the file
    line: int           # line number where the smell occurs
    type: str           # e.g. "Long Function", "Magic Number"
    severity: str        # "Low" | "Medium" | "High"
    explanation: str     # human-readable reason