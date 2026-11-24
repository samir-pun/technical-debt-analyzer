"""score_file() must work without loading any model."""

import pytest

from src.ml.risk import score_file

ROW = {"file": "x.py", "maintainability_index": 100, "complexity": 0, "code_smells": 10}


def test_score_file_needs_no_models():
    probs = {"large_class_probability": 0.0, "long_method_probability": 0.0}
    result = score_file(ROW, probs)
    assert result["composite_score"] == pytest.approx(0.35)
    assert result["risk_label"] == "MEDIUM"


def test_score_file_keeps_the_probabilities():
    probs = {"large_class_probability": 0.2, "long_method_probability": 0.4}
    result = score_file(ROW, probs)
    assert result["large_class_probability"] == 0.2
    assert result["long_method_probability"] == 0.4