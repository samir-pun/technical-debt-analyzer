"""
sensitivity.py

How much do the risk ratings depend on my hand-chosen weights and cut-offs?

Re-scores the same project under changed settings and reports, for each
scenario, how many files change rating, how well the file ranking is kept
(Spearman rank correlation) and whether the quality gate verdict changes.
The models run once per file, so large projects stay fast.

Run from the project root, with a folder path (default: sample_projects):
    python3 -m scripts.sensitivity [folder]
"""

from __future__ import annotations

import sys
import warnings

from scipy.stats import spearmanr

from src import config
from src.analyzer.analyzer import analyze_project
from src.ml.quality_gate import evaluate_quality_gate
from src.ml.risk import compute_smell_probabilities, score_file

# The weights used before they were rebalanced (model probability weighted most).
FIRST_WEIGHTS = {
    "smell_count": 0.10,
    "model_probability": 0.40,
    "maintainability": 0.30,
    "complexity": 0.20,
}
WEIGHT_STEP = 0.10
CUTOFF_STEP = 0.05


def _normalise(weights: dict) -> dict:
    total = sum(weights.values())
    return {name: value / total for name, value in weights.items()}


def _scenarios() -> list:
    base_weights = config.RISK_WEIGHTS
    base_cutoffs = (config.LOW_MAX, config.MEDIUM_MAX)
    scenarios = []

    for name in base_weights:
        for step in (WEIGHT_STEP, -WEIGHT_STEP):
            changed = dict(base_weights)
            changed[name] = max(0.0, changed[name] + step)
            scenarios.append((f"{name} weight {step:+.2f}", _normalise(changed), base_cutoffs))

    equal = {name: 1 / len(base_weights) for name in base_weights}
    scenarios.append(("equal weights", equal, base_cutoffs))
    scenarios.append(("first weights (model-heavy)", FIRST_WEIGHTS, base_cutoffs))

    for step in (-CUTOFF_STEP, CUTOFF_STEP):
        cutoffs = (base_cutoffs[0] + step, base_cutoffs[1] + step)
        scenarios.append((f"cut-offs {step:+.2f}", base_weights, cutoffs))

    return scenarios


def _rank_agreement(before: list, after: list):
    """Spearman correlation of two score lists, or None when it is not defined."""
    if len(before) < 3:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        rho = spearmanr(before, after).statistic
    return None if rho != rho else float(rho)  # rho != rho is true only for NaN


def main(path: str) -> None:
    rows = analyze_project(path).to_rows()
    if not rows:
        print(f"No analysable Python files found in {path}.")
        return

    probs = [compute_smell_probabilities(row) for row in rows]  # models run once

    def score_all(weights, thresholds):
        return [score_file(row, p, weights, thresholds) for row, p in zip(rows, probs)]

    baseline = score_all(config.RISK_WEIGHTS, (config.LOW_MAX, config.MEDIUM_MAX))
    base_labels = [r["risk_label"] for r in baseline]
    base_scores = [r["composite_score"] for r in baseline]
    counts = {label: base_labels.count(label) for label in ("HIGH", "MEDIUM", "LOW")}

    print(f"Project: {path}")
    print(f"Files: {len(rows)}  (HIGH {counts['HIGH']}, MEDIUM {counts['MEDIUM']}, LOW {counts['LOW']})")
    print(f"Baseline gate: {evaluate_quality_gate(baseline)['status']}")
    print()
    print(f"{'Scenario':<34}{'Changed':>8}{'%':>8}{'Spearman':>10}  Gate")
    print("-" * 68)

    for name, weights, thresholds in _scenarios():
        results = score_all(weights, thresholds)
        changed = sum(1 for before, r in zip(base_labels, results) if before != r["risk_label"])
        rho = _rank_agreement(base_scores, [r["composite_score"] for r in results])
        rho_text = "n/a" if rho is None else f"{rho:.3f}"
        gate = evaluate_quality_gate(results)["status"]
        print(f"{name:<34}{changed:>8}{100 * changed / len(rows):>7.0f}%{rho_text:>10}  {gate}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sample_projects")