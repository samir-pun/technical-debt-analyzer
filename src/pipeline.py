"""
pipeline.py

Single entry point for the whole system:
    input (folder / .zip / .py) -> analysis -> ML risk scoring
    -> ranking -> recommendations -> quality gate.

The dashboard only needs to call predict_project().

Run from the command line with:
    python3 -m src.pipeline <folder | .zip | .py>
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

from .analyzer.analyzer import analyze_project
from .analyzer.parser import IGNORED_DIR_NAMES
from .ml.quality_gate import evaluate_quality_gate
from .ml.risk import compute_risk
from .recommendations import generate_recommendations

MAX_EXTRACTED_BYTES = 200 * 1024 * 1024  # cap on uncompressed source code


def _extract_zip(zip_path: Path, dest: Path) -> None:
    """Extract only .py files from a zip, safely.

    Skips macOS metadata, ignored folders (venv, .git, node_modules, ...),
    unsafe paths, and refuses archives whose source code is too large.
    """
    dest = dest.resolve()
    total = 0
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            member = info.filename
            path = Path(member)
            if info.is_dir() or not member.endswith(".py"):
                continue
            if member.startswith("__MACOSX/") or path.name.startswith("._"):
                continue
            if any(part in IGNORED_DIR_NAMES for part in path.parts):
                continue
            target = (dest / member).resolve()
            if not target.is_relative_to(dest):
                raise ValueError(f"Unsafe path in zip file: {member}")
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise ValueError("Archive contains too much source code (limit 200 MB).")
            zf.extract(info, dest)


def predict_project(input_path: str | Path) -> dict:
    """Analyse a project and return ranked risk results plus the quality gate."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input not found: {input_path}")

    with tempfile.TemporaryDirectory(prefix="tda_") as tmp:
        work = Path(tmp)

        if input_path.is_dir():
            project_dir = input_path
        elif input_path.suffix == ".zip":
            _extract_zip(input_path, work)
            project_dir = work
        elif input_path.suffix == ".py":
            shutil.copy2(input_path, work)
            project_dir = work
        else:
            raise ValueError("Unsupported input: use a folder, a .zip or a .py file.")

        analysis = analyze_project(project_dir)

        files = []
        for file_result, row in zip(analysis.files, analysis.to_rows()):
            risk = compute_risk(row)
            entry = {
                **risk,
                "loc": row["loc"],
                "complexity": row["complexity"],
                "maintainability_index": row["maintainability_index"],
                "code_smells": row["code_smells"],
                "smell_breakdown": dict(Counter(s.type for s in file_result.smells)),
            }
            entry["recommendations"] = generate_recommendations(entry)
            files.append(entry)

    # Highest risk first, so the developer knows what to fix first.
    files.sort(key=lambda f: f["composite_score"], reverse=True)
    for rank, f in enumerate(files, start=1):
        f["rank"] = rank

    project_name = input_path.stem if input_path.is_file() else input_path.name
    return {
        "project_name": project_name,
        "files": files,
        "quality_gate": evaluate_quality_gate(files),
    }


def _print_report(result: dict) -> None:
    print(f"\nProject: {result['project_name']}")
    print(f"{'Rank':<5}{'Risk':<8}{'Score':<8}{'Smells':<8}File")
    print("-" * 70)
    for f in result["files"]:
        print(f"{f['rank']:<5}{f['risk_label']:<8}{f['composite_score']:<8}"
              f"{f['code_smells']:<8}{f['file']}")
    gate = result["quality_gate"]
    print(f"\nQuality gate: {gate['status']}  (average score {gate['average_score']})")
    for reason in gate["reasons"]:
        print(f"  - {reason}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 -m src.pipeline <folder | .zip | .py>")
        sys.exit(1)
    _print_report(predict_project(sys.argv[1]))