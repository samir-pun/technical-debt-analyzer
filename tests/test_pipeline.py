"""Tests for the prediction pipeline: input types, zip safety and error handling."""

import zipfile
from pathlib import Path

import pytest

from src import pipeline
from src.pipeline import predict_project

SAMPLES = Path(__file__).resolve().parents[1] / "sample_projects"
GOOD = "def add(a, b):\n    return a + b\n"


def make_zip(path, members):
    """Write a zip containing {name: text} members."""
    with zipfile.ZipFile(path, "w") as zf:
        for name, text in members.items():
            zf.writestr(name, text)
    return path


def test_single_py_file_is_analysed():
    result = predict_project(SAMPLES / "low_risk" / "calculator.py")
    assert [f["file"] for f in result["files"]] == ["calculator.py"]
    assert result["files"][0]["risk_label"] == "LOW"
    assert result["quality_gate"]["status"] == "PASS"


def test_zip_gives_the_same_scores_as_the_folder(tmp_path):
    archive = tmp_path / "samples.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for path in SAMPLES.rglob("*.py"):
            zf.write(path, path.relative_to(SAMPLES.parent))

    from_folder = {f["file"].split("/")[-1]: f["composite_score"]
                   for f in predict_project(SAMPLES)["files"]}
    from_zip = {f["file"].split("/")[-1]: f["composite_score"]
                for f in predict_project(archive)["files"]}

    assert from_zip == from_folder


def test_zip_skips_ignored_folders_macos_junk_and_non_python(tmp_path):
    archive = make_zip(tmp_path / "project.zip", {
        "good.py": GOOD,
        "venv/lib/junk.py": GOOD,
        "node_modules/pkg/x.py": GOOD,
        "__MACOSX/._good.py": "not python",
        "notes.txt": "hello",
    })

    result = predict_project(archive)

    assert [f["file"] for f in result["files"]] == ["good.py"]


def test_zip_with_unsafe_path_is_rejected(tmp_path):
    archive = make_zip(tmp_path / "evil.zip", {"../evil.py": GOOD})
    with pytest.raises(ValueError, match="Unsafe"):
        predict_project(archive)


def test_zip_over_the_size_cap_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(pipeline, "MAX_EXTRACTED_BYTES", 10)
    archive = make_zip(tmp_path / "big.zip", {"big.py": GOOD})
    with pytest.raises(ValueError, match="too much source code"):
        predict_project(archive)


def test_missing_path_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        predict_project(tmp_path / "nothing_here.zip")


def test_unsupported_file_type_is_rejected(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported"):
        predict_project(notes)


def test_every_file_has_recommendations_and_a_smell_breakdown():
    for f in predict_project(SAMPLES)["files"]:
        assert f["recommendations"]
        assert "smell_breakdown" in f