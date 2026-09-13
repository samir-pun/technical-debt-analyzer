"""
duplicate_code.py

Detects duplicated blocks of code within a single file, using a
sliding window of normalized lines, hashed for comparison.
"""

from __future__ import annotations

import hashlib
from typing import List

from .models import Smell

BLOCK_SIZE = 6  # consecutive lines considered a "block"


def _normalized_lines(source: str) -> List[str]:
    lines = []
    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def detect_duplicate_code(source: str, relative_path: str, block_size: int = BLOCK_SIZE) -> List[Smell]:
    lines = _normalized_lines(source)
    if len(lines) < block_size * 2:
        return []

    seen_hashes = {}
    smells: List[Smell] = []
    next_allowed_start = 0

    for start in range(0, len(lines) - block_size + 1):
        block = "\n".join(lines[start:start + block_size])
        block_hash = hashlib.sha1(block.encode("utf-8")).hexdigest()

        if block_hash in seen_hashes:
            first_start = seen_hashes[block_hash]
            if start - first_start >= block_size and start >= next_allowed_start:
                smells.append(
                    Smell(
                        file=relative_path,
                        line=start + 1,
                        type="Duplicate Code",
                        severity="Medium",
                        explanation=(
                            f"Block of {block_size}+ lines appears to duplicate code "
                            f"found earlier in the same file (near line {first_start + 1})."
                        ),
                    )
                )
                next_allowed_start = start + block_size
        else:
            seen_hashes[block_hash] = start

    return smells