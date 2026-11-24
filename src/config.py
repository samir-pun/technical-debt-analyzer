"""
config.py

Every number that decides a file's risk rating or the project's quality
gate, in one place.

These values were chosen by hand and have not been validated against
labelled data. Keeping them here makes it possible to test how sensitive
the ratings are to each choice.
"""

# Weight of each risk factor in the composite score. They add up to 1.0.
RISK_WEIGHTS = {
    "smell_count": 0.35,        # my four rule-based detectors
    "model_probability": 0.25,  # average of the two Random Forest models
    "maintainability": 0.25,    # (100 - maintainability index) / 100
    "complexity": 0.15,         # average cyclomatic complexity / COMPLEXITY_CAP
}

# A factor counts as maximum risk at these values (its factor is then 1.0).
SMELL_COUNT_CAP = 10
COMPLEXITY_CAP = 20

# Score cut-offs: below LOW_MAX is LOW, below MEDIUM_MAX is MEDIUM, else HIGH.
LOW_MAX = 0.33
MEDIUM_MAX = 0.66

# Quality gate: the project fails if any limit is exceeded.
MAX_HIGH_RISK_FILES = 0     # any HIGH file fails the gate
MAX_ELEVATED_RATIO = 0.5    # largest allowed share of MEDIUM + HIGH files
MAX_AVERAGE_SCORE = 0.5     # largest allowed average composite score