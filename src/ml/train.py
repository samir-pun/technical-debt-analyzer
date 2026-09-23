"""
train.py

Phase 8.2 / 10 / 11 — Train and evaluate Logistic Regression and
Random Forest on the Sandouka & Aljamaan Python Code Smell Dataset,
for both the Large Class and Long Method variants.

Run with: python3 -m src.ml.train
"""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATASETS = {
    "Large Class": {
        "path": "data/raw/Python_LargeClassSmell_Dataset.csv",
        "label_column": "LargeClass",
    },
    "Long Method": {
        "path": "data/raw/Python_LongMethodSmell_Dataset.csv",
        "label_column": "Experince Based ",  # note: dataset's actual column has a typo + trailing space
    },
}


def load_data(path: str, label_column: str):
    df = pd.read_csv(path)
    X = df.drop(columns=[label_column])
    y = df[label_column]
    return X, y


def train_and_evaluate(path: str, label_column: str):
    X, y = load_data(path, label_column)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = {}

    log_reg = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
    log_reg.fit(X_train_scaled, y_train)
    y_pred_lr = log_reg.predict(X_test_scaled)

    results["Logistic Regression"] = {
        "accuracy": accuracy_score(y_test, y_pred_lr),
        "precision": precision_score(y_test, y_pred_lr),
        "recall": recall_score(y_test, y_pred_lr),
        "f1": f1_score(y_test, y_pred_lr),
        "confusion_matrix": confusion_matrix(y_test, y_pred_lr).tolist(),
    }

    rf = RandomForestClassifier(class_weight="balanced", n_estimators=200, random_state=42)
    rf.fit(X_train, y_train)
    y_pred_rf = rf.predict(X_test)

    results["Random Forest"] = {
        "accuracy": accuracy_score(y_test, y_pred_rf),
        "precision": precision_score(y_test, y_pred_rf),
        "recall": recall_score(y_test, y_pred_rf),
        "f1": f1_score(y_test, y_pred_rf),
        "confusion_matrix": confusion_matrix(y_test, y_pred_rf).tolist(),
    }

    return results, log_reg, rf, scaler


def print_results(dataset_name: str, results: dict):
    print(f"\n{'=' * 50}")
    print(f"DATASET: {dataset_name}")
    print(f"{'=' * 50}")
    for model_name, metrics in results.items():
        print(f"\n{model_name}")
        print(f"  Accuracy:  {metrics['accuracy']:.3f}")
        print(f"  Precision: {metrics['precision']:.3f}")
        print(f"  Recall:    {metrics['recall']:.3f}")
        print(f"  F1 Score:  {metrics['f1']:.3f}")
        print(f"  Confusion Matrix: {metrics['confusion_matrix']}")


def print_feature_importance(dataset_name: str, rf: RandomForestClassifier, feature_names):
    print(f"\n{dataset_name} — Random Forest feature importance (top 5):")
    importances = sorted(zip(feature_names, rf.feature_importances_), key=lambda x: -x[1])
    for name, score in importances[:5]:
        print(f"  {name:<20} {score:.3f}")


import joblib
from pathlib import Path

MODELS_DIR = Path("src/ml/saved_models")


def save_model(dataset_name: str, model, scaler):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = dataset_name.lower().replace(" ", "_")
    joblib.dump(model, MODELS_DIR / f"{safe_name}_random_forest.joblib")
    joblib.dump(scaler, MODELS_DIR / f"{safe_name}_scaler.joblib")
    print(f"  Saved model to {MODELS_DIR / f'{safe_name}_random_forest.joblib'}")


if __name__ == "__main__":
    for dataset_name, config in DATASETS.items():
        X, y = load_data(config["path"], config["label_column"])
        results, _, rf, scaler = train_and_evaluate(config["path"], config["label_column"])
        print_results(dataset_name, results)
        print_feature_importance(dataset_name, rf, X.columns)
        save_model(dataset_name, rf, scaler)