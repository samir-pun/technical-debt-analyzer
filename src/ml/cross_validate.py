"""
cross_validate.py

5-fold stratified cross-validation for Logistic Regression and Random
Forest on both smell datasets (proposal deliverable).

Run with: python3 -m src.ml.cross_validate
"""

from __future__ import annotations

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .train import DATASETS, load_data

SCORING = ["accuracy", "precision", "recall", "f1"]
F1_TARGET = 0.75  # target stated in the project proposal


def run_cross_validation(path: str, label_column: str) -> dict:
    X, y = load_data(path, label_column)

    # Stratified: every fold keeps the same smelly / not-smelly ratio.
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    models = {
        # Scaler lives inside the pipeline so it is fitted per fold (no leakage).
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        ),
        "Random Forest": RandomForestClassifier(
            class_weight="balanced", n_estimators=200, random_state=42
        ),
    }

    results = {}
    for model_name, model in models.items():
        scores = cross_validate(model, X, y, cv=cv, scoring=SCORING)
        results[model_name] = {
            metric: (scores[f"test_{metric}"].mean(), scores[f"test_{metric}"].std())
            for metric in SCORING
        }
    return results


def print_cv_results(dataset_name: str, results: dict):
    print(f"\n{'=' * 55}")
    print(f"5-FOLD CROSS-VALIDATION: {dataset_name}")
    print(f"{'=' * 55}")
    for model_name, metrics in results.items():
        print(f"\n{model_name}")
        for metric, (mean, std) in metrics.items():
            print(f"  {metric.capitalize():<10} {mean:.3f} (+/- {std:.3f})")
        f1_mean = metrics["f1"][0]
        verdict = "MEETS" if f1_mean >= F1_TARGET else "BELOW"
        print(f"  -> F1 {f1_mean:.3f} {verdict} the {F1_TARGET} target")


if __name__ == "__main__":
    for dataset_name, config in DATASETS.items():
        results = run_cross_validation(config["path"], config["label_column"])
        print_cv_results(dataset_name, results)