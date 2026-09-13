"""
detector.py

Orchestrates all individual smell detectors for a single parsed file.
Adding a new detector later: write the module, import it here, add one
line to run_all_detectors(). Nothing else needs to change.
"""

from __future__ import annotations

from typing import List

from ..parser import ParsedFile
from .duplicate_code import detect_duplicate_code
from .long_function import detect_long_functions
from .magic_number import detect_magic_numbers
from .models import Smell
from .naming import detect_naming_issues


def run_all_detectors(parsed_file: ParsedFile) -> List[Smell]:
    """Run every registered smell detector against one parsed file."""
    if parsed_file.tree is None:
        return []

    smells: List[Smell] = []
    smells.extend(detect_long_functions(parsed_file.tree, parsed_file.relative_path))
    smells.extend(detect_magic_numbers(parsed_file.tree, parsed_file.relative_path))
    smells.extend(detect_naming_issues(parsed_file.tree, parsed_file.relative_path))
    smells.extend(detect_duplicate_code(parsed_file.source, parsed_file.relative_path))
    return smells