"""
risk.py

Combines the two trained smell-detection models with the analyser's own
metrics into one composite LOW / MEDIUM / HIGH risk verdict per file.

The weights, caps and cut-offs live in src/config.py.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from .. import config

MODELS_DIR = Path("src/ml/saved_models")

# Must match the exact column order the models were trained on
# (the CSV columns, minus the label column).
FEATURE_ORDER = [
    "loc", "lloc", "scloc", "comments", "single_comments", "multi_comments",
    "blanks", "h1", "h2", "n1", "n2", "vocabulary", "length",
    "calculated_length", "volume", "difficulty", "effort", "time", "bugs",
]

_large_class_model = None
_long_method_model = None


def _load_models():
    """Load both trained models once, cache them for reuse."""
    global _large_class_model, _long_method_model
    if _large_class_model is None:
        _large_class_model = joblib.load(MODELS_DIR / "large_class_random_forest.joblib")
    if _long_method_model is None:
        _long_method_model = joblib.load(MODELS_DIR / "long_method_random_forest.joblib")
    return _large_class_model, _long_method_model


def _extract_features(row: dict) -> pd.DataFrame:
    """Pull just the model's expected features, in the correct order."""
    return pd.DataFrame([{key: row[key] for key in FEATURE_ORDER}])


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_smell_probabilities(row: dict) -> dict:
    """Return each model's predicted probability that this file has that smell."""
    large_class_model, long_method_model = _load_models()
    X = _extract_features(row)

    large_class_proba = large_class_model.predict_proba(X)[0][1]
    long_method_proba = long_method_model.predict_proba(X)[0][1]

    return {
        "large_class_probability": round(float(large_class_proba), 3),
        "long_method_probability": round(float(long_method_proba), 3),
    }


def score_file(
    row: dict,
    probs: dict,
    weights: dict | None = None,
    thresholds: tuple[float, float] | None = None,
) -> dict:
    """
    Turn a file's metrics and its model probabilities into a 0-1 composite
    score and a LOW / MEDIUM / HIGH label. No models are run here.

    weights and thresholds default to the values in src/config.py. Passing
    others lets an experiment re-score the same files without editing code.

    The smell count carries the largest weight because it covers four smell
    types, while the models cover only two narrow, size-based smells.
    """
    weights = weights or config.RISK_WEIGHTS
    low_max, medium_max = thresholds or (config.LOW_MAX, config.MEDIUM_MAX)

    smell_probability = (probs["large_class_probability"] + probs["long_method_probability"]) / 2

    maintainability_factor = _clamp((100 - row["maintainability_index"]) / 100)
    complexity_factor = _clamp(row["complexity"] / config.COMPLEXITY_CAP)
    smell_count_factor = _clamp(row["code_smells"] / config.SMELL_COUNT_CAP)

    composite_score = (
        weights["model_probability"] * smell_probability
        + weights["maintainability"] * maintainability_factor
        + weights["complexity"] * complexity_factor
        + weights["smell_count"] * smell_count_factor
    )

    if composite_score < low_max:
        risk_label = "LOW"
    elif composite_score < medium_max:
        risk_label = "MEDIUM"
    else:
        risk_label = "HIGH"

    return {
        "file": row["file"],
        "composite_score": round(composite_score, 3),
        "risk_label": risk_label,
        **probs,
    }


def compute_risk(
    row: dict,
    weights: dict | None = None,
    thresholds: tuple[float, float] | None = None,
) -> dict:
    """Run both models on a file, then score it."""
    return score_file(row, compute_smell_probabilities(row), weights, thresholds)