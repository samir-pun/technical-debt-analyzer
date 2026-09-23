"""
loc.py

Lines-of-code metrics, via radon's raw analysis module.

Using radon here (instead of purely custom logic) means our field names
and definitions exactly match the Sandouka & Aljamaan Python Code Smell
Dataset, which was very likely built the same way — critical for being
able to apply models trained on that dataset to our own analyzer's output.
"""

from __future__ import annotations

from dataclasses import dataclass

from radon.raw import analyze


@dataclass
class LocResult:
    total_loc: int          # radon calls this 'loc' - total lines
    lloc: int                # logical lines of code
    sloc: int                # source lines of code (excludes blank/comment)
    comments: int             # comment lines
    single_comments: int       # single-line comments
    multi_comments: int        # multi-line string/comment lines
    blank_loc: int             # blank lines


def calculate_loc(source: str) -> LocResult:
    """Calculate raw line metrics using radon, matching external dataset fields."""
    try:
        raw = analyze(source)
    except SyntaxError:
        return LocResult(0, 0, 0, 0, 0, 0, 0)

    return LocResult(
        total_loc=raw.loc,
        lloc=raw.lloc,
        sloc=raw.sloc,
        comments=raw.comments,
        single_comments=raw.single_comments,
        multi_comments=raw.multi,
        blank_loc=raw.blank,
    )