"""Checks on the central configuration and on overriding it."""

import pytest

from src import config
from src.ml import risk
from src.ml.risk import compute_risk

# Ten smells, otherwise a perfect file: with the default weights the score is 0.35.
ROW = {"file": "x.py", "maintainability_index": 100, "complexity": 0, "code_smells": 10}


def fixed_probabilities(monkeypatch, value):
    monkeypatch.setattr(
        risk,
        "compute_smell_probabilities",
        lambda row: {"large_class_probability": value, "long_method_probability": value},
    )


def test_weights_add_up_to_one():
    assert sum(config.RISK_WEIGHTS.values()) == pytest.approx(1.0)


def test_thresholds_are_ordered():
    assert 0 < config.LOW_MAX < config.MEDIUM_MAX < 1


def test_gate_limits_are_in_range():
    assert config.MAX_HIGH_RISK_FILES >= 0
    assert 0 <= config.MAX_ELEVATED_RATIO <= 1
    assert 0 <= config.MAX_AVERAGE_SCORE <= 1


def test_default_weights_rate_ten_smells_medium(monkeypatch):
    fixed_probabilities(monkeypatch, 0.0)
    result = compute_risk(ROW)
    assert result["composite_score"] == pytest.approx(0.35)
    assert result["risk_label"] == "MEDIUM"


def test_custom_weights_change_the_score(monkeypatch):
    fixed_probabilities(monkeypatch, 0.0)
    only_model = {
        "smell_count": 0.0,
        "model_probability": 1.0,
        "maintainability": 0.0,
        "complexity": 0.0,
    }
    result = compute_risk(ROW, weights=only_model)
    assert result["composite_score"] == 0
    assert result["risk_label"] == "LOW"


def test_custom_thresholds_change_the_label(monkeypatch):
    fixed_probabilities(monkeypatch, 0.0)
    result = compute_risk(ROW, thresholds=(0.5, 0.9))
    assert result["risk_label"] == "LOW"