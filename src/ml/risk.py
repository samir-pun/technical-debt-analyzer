"""
risk.py

Phase 8 (final part) / Phase 13 — Combines the two trained smell-detection
models with our own analyzer's metrics into one composite LOW/MEDIUM/HIGH
risk verdict per file.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

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


def compute_risk(row: dict) -> dict:
    """
    Combine ML smell predictions with our own analyzer's metrics into
    one composite risk score (0-1) and a LOW/MEDIUM/HIGH label.

    Weights reflect that our own smell_count covers 4 smell types
    (naming, magic numbers, duplication, long functions), while the
    ML models only cover 2 narrow, size-based smells (Large Class,
    Long Method) — so smell_count is weighted more heavily as the
    more comprehensive signal.
    """
    probs = compute_smell_probabilities(row)
    smell_probability = (probs["large_class_probability"] + probs["long_method_probability"]) / 2

    maintainability_factor = max(0.0, min(1.0, (100 - row["maintainability_index"]) / 100))
    complexity_factor = max(0.0, min(1.0, row["complexity"] / 20))
    smell_count_factor = max(0.0, min(1.0, row["code_smells"] / 10))

    composite_score = (
        0.25 * smell_probability
        + 0.25 * maintainability_factor
        + 0.15 * complexity_factor
        + 0.35 * smell_count_factor
    )

    if composite_score < 0.33:
        risk_label = "LOW"
    elif composite_score < 0.66:
        risk_label = "MEDIUM"
    else:
        risk_label = "HIGH"

    return {
        "file": row["file"],
        "composite_score": round(composite_score, 3),
        "risk_label": risk_label,
        **probs,
    }