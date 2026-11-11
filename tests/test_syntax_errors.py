
"""A file that cannot be parsed must be reported as not analysed, never scored."""

from pathlib import Path

from src.analyzer.analyzer import analyze_project
from src.pipeline import predict_project

GOOD = "def add(a, b):\n    return a + b\n"
BROKEN = "def f()\n    pass\n"
SAMPLES = Path(__file__).resolve().parents[1] / "sample_projects"


def test_broken_file_is_listed_as_skipped(tmp_path):
    (tmp_path / "good.py").write_text(GOOD)
    (tmp_path / "broken.py").write_text(BROKEN)

    analysis = analyze_project(tmp_path)

    assert [f.relative_path for f in analysis.files] == ["good.py"]
    assert len(analysis.skipped) == 1
    assert analysis.skipped[0]["file"] == "broken.py"
    assert "SyntaxError" in analysis.skipped[0]["error"]


def test_broken_file_gets_no_risk_score(tmp_path):
    (tmp_path / "good.py").write_text(GOOD)
    (tmp_path / "broken.py").write_text(BROKEN)

    result = predict_project(tmp_path)

    assert [f["file"] for f in result["files"]] == ["good.py"]
    assert result["skipped"][0]["file"] == "broken.py"


def test_project_with_only_broken_files_fails_the_gate(tmp_path):
    (tmp_path / "broken.py").write_text(BROKEN)

    result = predict_project(tmp_path)

    assert result["files"] == []
    assert result["quality_gate"]["status"] == "FAIL"
    assert len(result["skipped"]) == 1


def test_clean_project_has_nothing_skipped():
    assert predict_project(SAMPLES)["skipped"] == []