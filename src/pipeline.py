"""
pipeline.py

Single entry point for the whole system:
    input (folder / .zip / .py) -> analysis -> ML risk scoring
    -> ranking -> quality gate.

The dashboard only needs to call predict_project().

Run from the command line with:
    python3 -m src.pipeline <folder | .zip | .py>
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from .analyzer.analyzer import analyze_project
from .ml.quality_gate import evaluate_quality_gate
from .ml.risk import compute_risk


def _extract_zip(zip_path: Path, dest: Path) -> None:
    """Extract a zip safely, skipping macOS metadata and unsafe paths."""
    dest = dest.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            # macOS adds resource-fork junk to zips; it is not real source code.
            if member.startswith("__MACOSX/") or Path(member).name.startswith("._"):
                continue
            target = (dest / member).resolve()
            if not target.is_relative_to(dest):
                raise ValueError(f"Unsafe path in zip file: {member}")
            zf.extract(member, dest)


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
        for row in analysis.to_rows():
            risk = compute_risk(row)
            files.append({
                **risk,
                "loc": row["loc"],
                "complexity": row["complexity"],
                "maintainability_index": row["maintainability_index"],
                "code_smells": row["code_smells"],
            })

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