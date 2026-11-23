"""Tests for the composite risk score and its LOW / MEDIUM / HIGH tiers."""

from pathlib import Path

import pytest

from src.ml import risk
from src.pipeline import predict_project

SAMPLES = Path(__file__).resolve().parents[1] / "sample_projects"


def score_row(monkeypatch, probability, mi, complexity, smells):
    """Run compute_risk() with the model probabilities fixed, so only the formula is tested."""
    monkeypatch.setattr(
        risk,
        "compute_smell_probabilities",
        lambda row: {
            "large_class_probability": probability,
            "long_method_probability": probability,
        },
    )
    row = {
        "file": "x.py",
        "maintainability_index": mi,
        "complexity": complexity,
        "code_smells": smells,
    }
    return risk.compute_risk(row)


def test_lowest_possible_risk_is_low(monkeypatch):
    result = score_row(monkeypatch, probability=0.0, mi=100, complexity=0, smells=0)
    assert result["composite_score"] == 0
    assert result["risk_label"] == "LOW"


def test_highest_possible_risk_is_high(monkeypatch):
    result = score_row(monkeypatch, probability=1.0, mi=0, complexity=20, smells=10)
    assert result["composite_score"] == pytest.approx(1.0)
    assert result["risk_label"] == "HIGH"


def test_extreme_inputs_are_clamped(monkeypatch):
    result = score_row(monkeypatch, probability=1.0, mi=-50, complexity=500, smells=500)
    assert result["composite_score"] == pytest.approx(1.0)


def test_smell_count_alone_crosses_the_medium_boundary(monkeypatch):
    # With every other factor at zero, the score is 0.35 x (smells / 10).
    below = score_row(monkeypatch, 0.0, mi=100, complexity=0, smells=9)
    above = score_row(monkeypatch, 0.0, mi=100, complexity=0, smells=10)
    assert below["risk_label"] == "LOW"       # 0.315
    assert above["risk_label"] == "MEDIUM"    # 0.350


def test_high_boundary(monkeypatch):
    # Model, maintainability and complexity at maximum give 0.65, just under HIGH.
    below = score_row(monkeypatch, 1.0, mi=0, complexity=20, smells=0)
    above = score_row(monkeypatch, 1.0, mi=0, complexity=20, smells=1)
    assert below["risk_label"] == "MEDIUM"    # 0.650
    assert above["risk_label"] == "HIGH"      # 0.685


def test_sample_projects_land_in_the_expected_tiers():
    result = predict_project(SAMPLES)
    by_name = {f["file"].split("/")[-1]: f for f in result["files"]}

    assert by_name["calculator.py"]["risk_label"] == "LOW"
    assert by_name["legacy_payment.py"]["risk_label"] == "MEDIUM"
    assert by_name["massive_legacy_system.py"]["risk_label"] == "HIGH"


def test_sample_scores_match_the_reported_values():
    result = predict_project(SAMPLES)
    scores = {f["file"].split("/")[-1]: f["composite_score"] for f in result["files"]}

    assert scores["calculator.py"] == pytest.approx(0.116, abs=0.002)
    assert scores["legacy_payment.py"] == pytest.approx(0.548, abs=0.002)
    assert scores["massive_legacy_system.py"] == pytest.approx(0.702, abs=0.002)


def test_files_are_ranked_from_highest_to_lowest_risk():
    files = predict_project(SAMPLES)["files"]
    scores = [f["composite_score"] for f in files]

    assert scores == sorted(scores, reverse=True)
    assert [f["rank"] for f in files] == [1, 2, 3]