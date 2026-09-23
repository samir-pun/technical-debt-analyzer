"""
analyzer.py

The single public entry point for the static analysis engine.
Combines parsing (Phase 3) + metrics (Phase 4) + smells (Phase 5)
into one structured result per file, and per project.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .metrics.complexity import ComplexityResult, calculate_complexity
from .metrics.halstead import HalsteadResult, calculate_halstead
from .metrics.loc import LocResult, calculate_loc
from .metrics.maintainability import MaintainabilityResult, calculate_maintainability
from .parser import ParsedFile, load_project
from .smells.detector import run_all_detectors
from .smells.models import Smell


@dataclass
class FileAnalysisResult:
    """All metrics + smells for a single file — one row of the dataset."""
    relative_path: str
    loc: LocResult
    complexity: ComplexityResult
    maintainability: MaintainabilityResult
    halstead: HalsteadResult
    smells: List[Smell] = field(default_factory=list)

    @property
    def smell_count(self) -> int:
        return len(self.smells)


@dataclass
class ProjectAnalysisResult:
    """Aggregate result for an entire project."""
    project_name: str
    files: List[FileAnalysisResult] = field(default_factory=list)

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_loc(self) -> int:
        return sum(f.loc.total_loc for f in self.files)

    @property
    def total_smells(self) -> int:
        return sum(f.smell_count for f in self.files)

    @property
    def average_maintainability(self) -> float:
        if not self.files:
            return 0.0
        return sum(f.maintainability.score for f in self.files) / len(self.files)

    def to_rows(self) -> List[dict]:
        """
        Flatten into a row shaped to match the Sandouka & Aljamaan dataset's
        feature columns exactly (loc, lloc, scloc, comments, ..., h1, h2, ...),
        plus our own extra fields (complexity, maintainability_index, code_smells)
        appended at the end.
        """
        rows = []
        for f in self.files:
            rows.append({
                # --- fields matching the external dataset's columns ---
                "loc": f.loc.total_loc,
                "lloc": f.loc.lloc,
                "scloc": f.loc.sloc,
                "comments": f.loc.comments,
                "single_comments": f.loc.single_comments,
                "multi_comments": f.loc.multi_comments,
                "blanks": f.loc.blank_loc,
                "h1": f.halstead.h1,
                "h2": f.halstead.h2,
                "n1": f.halstead.n1,
                "n2": f.halstead.n2,
                "vocabulary": f.halstead.vocabulary,
                "length": f.halstead.length,
                "calculated_length": f.halstead.calculated_length,
                "volume": f.halstead.volume,
                "difficulty": f.halstead.difficulty,
                "effort": f.halstead.effort,
                "time": f.halstead.time,
                "bugs": f.halstead.bugs,
                # --- our own extra fields, not in the external dataset ---
                "file": f.relative_path,
                "complexity": round(f.complexity.average_complexity, 2),
                "maintainability_index": round(f.maintainability.score, 2),
                "code_smells": f.smell_count,
            })
        return rows


def _analyze_single_file(parsed_file: ParsedFile) -> FileAnalysisResult:
    smells = run_all_detectors(parsed_file) if parsed_file.tree else []
    return FileAnalysisResult(
        relative_path=parsed_file.relative_path,
        loc=calculate_loc(parsed_file.source),
        complexity=calculate_complexity(parsed_file.source),
        maintainability=calculate_maintainability(parsed_file.source),
        halstead=calculate_halstead(parsed_file.source),
        smells=smells,
    )


def analyze_project(input_path: str | Path) -> ProjectAnalysisResult:
    """Run the full static analysis pipeline on a project folder."""
    input_path = Path(input_path)
    parsed_files = load_project(input_path)

    result = ProjectAnalysisResult(project_name=input_path.name)
    for parsed_file in parsed_files:
        result.files.append(_analyze_single_file(parsed_file))

    return result