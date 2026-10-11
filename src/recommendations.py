"""
recommendations.py

Turns a file's metrics, smell counts and ML predictions into plain-language
refactoring advice. Rule-based: every recommendation comes from the same
measurements that produced the risk score, so advice is traceable to evidence.
"""

from __future__ import annotations

from typing import List

# Radon complexity bands: 1-5 A, 6-10 B, 11-20 C, so above 10 is "moderate" or worse.
COMPLEXITY_THRESHOLD = 10
# Radon maintainability ranks: 20-100 is A, below 20 is B or worse.
MAINTAINABILITY_THRESHOLD = 20
# 0.5 is the default decision boundary for a predicted probability.
ML_THRESHOLD = 0.5

SMELL_ADVICE = {
    "Long Function": "Split {n} long function(s) into smaller, single-purpose functions.",
    "Magic Number": "Replace {n} hard-coded number(s) with named constants.",
    "Poor Naming": "Rename {n} identifier(s) to follow PEP 8 (snake_case functions, PascalCase classes).",
    "Duplicate Code": "Extract {n} duplicated block(s) into shared functions.",
}


def generate_recommendations(file_info: dict) -> List[str]:
    recs: List[str] = []

    long_method_p = file_info.get("long_method_probability", 0.0)
    large_class_p = file_info.get("large_class_probability", 0.0)
    if long_method_p >= ML_THRESHOLD:
        recs.append(
            f"The model predicts long-method smells (probability {long_method_p:.2f}): "
            "break up the longest functions."
        )
    if large_class_p >= ML_THRESHOLD:
        recs.append(
            f"The model predicts a large-class smell (probability {large_class_p:.2f}): "
            "split classes that handle several responsibilities."
        )

    complexity = file_info.get("complexity", 0)
    if complexity > COMPLEXITY_THRESHOLD:
        recs.append(
            f"Average cyclomatic complexity is {complexity}, above {COMPLEXITY_THRESHOLD}: "
            "simplify nested conditions and loops."
        )

    mi = file_info.get("maintainability_index", 100)
    if mi < MAINTAINABILITY_THRESHOLD:
        recs.append(
            f"Maintainability index is {mi}, below {MAINTAINABILITY_THRESHOLD}: "
            "refactor this file before adding new features."
        )

    breakdown = file_info.get("smell_breakdown", {})
    for smell_type, count in sorted(breakdown.items(), key=lambda kv: -kv[1]):
        template = SMELL_ADVICE.get(smell_type)
        if template:
            recs.append(template.format(n=count))

    if not recs:
        recs.append("No refactoring needed: no thresholds were exceeded.")
    return recs