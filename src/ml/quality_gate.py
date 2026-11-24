"""
quality_gate.py

Project-level PASS / FAIL decision built on per-file risk results.

The limits live in src/config.py. They are design decisions, modelled on
the threshold-based quality gates used by tools such as SonarQube.
"""

from __future__ import annotations

from typing import List

from .. import config


def evaluate_quality_gate(risk_results: List[dict]) -> dict:
    """Takes a list of compute_risk() outputs, returns a PASS/FAIL verdict."""
    total = len(risk_results)
    if total == 0:
        return {
            "status": "FAIL",
            "reasons": ["No files were analysed."],
            "total_files": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "average_score": 0.0,
        }

    high = sum(1 for r in risk_results if r["risk_label"] == "HIGH")
    medium = sum(1 for r in risk_results if r["risk_label"] == "MEDIUM")
    low = sum(1 for r in risk_results if r["risk_label"] == "LOW")
    average_score = sum(r["composite_score"] for r in risk_results) / total
    elevated_ratio = (high + medium) / total

    reasons = []
    if high > config.MAX_HIGH_RISK_FILES:
        reasons.append(
            f"{high} file(s) rated HIGH risk (allowed: {config.MAX_HIGH_RISK_FILES})."
        )
    if elevated_ratio > config.MAX_ELEVATED_RATIO:
        reasons.append(
            f"{elevated_ratio:.0%} of files are MEDIUM or HIGH risk "
            f"(allowed: {config.MAX_ELEVATED_RATIO:.0%})."
        )
    if average_score > config.MAX_AVERAGE_SCORE:
        reasons.append(
            f"Average risk score {average_score:.3f} exceeds {config.MAX_AVERAGE_SCORE}."
        )

    return {
        "status": "FAIL" if reasons else "PASS",
        "reasons": reasons,
        "total_files": total,
        "high": high,
        "medium": medium,
        "low": low,
        "average_score": round(average_score, 3),
    }