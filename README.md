# Technical Debt Analyzer

A web tool that finds technical debt in Python code. It measures each file, flags known bad patterns, asks two trained models whether the file looks like a Large Class or a Long Method, and combines everything into a LOW, MEDIUM or HIGH risk rating per file. The files are ranked, and the whole project gets a pass or fail quality gate.

Final year project, University of Bedfordshire. Author: Samir Pun.

## What it does

1. **Reads** every `.py` file in a folder, a zip archive or a single file, and parses it with Python's `ast` module.
2. **Measures** lines of code, cyclomatic complexity, maintainability index and Halstead metrics with Radon.
3. **Flags** four smells with rule-based detectors: long functions, magic numbers, poor naming and duplicated code.
4. **Predicts** Large Class and Long Method smells with two Random Forest models.
5. **Scores** each file from 0 to 1 and rates it LOW (below 0.33), MEDIUM (below 0.66) or HIGH.
6. **Ranks** the files, gives refactoring advice, and applies a project-level quality gate.

Files that cannot be parsed (for example, syntax errors) are listed as "not analysed" and receive no score.

## Install

Tested on macOS with Python 3.14.

```
git clone https://github.com/samir-pun/technical-debt-analyzer.git
cd technical-debt-analyzer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

On Windows, activate the environment with `venv\Scripts\activate`.

## Use

Web dashboard:

```
python3 -m src.app.app
```

Open http://127.0.0.1:5001, upload a `.py` file or a `.zip`, and read the results. Uploads can be up to 500 MB. Inside a zip only `.py` files are extracted, and folders such as `venv`, `.git` and `node_modules` are skipped.

Command line:

```
python3 -m src.pipeline path/to/project
```

## Tests

```
python3 -m pytest
```

Expected result: 13 passed and 1 expected failure. The expected failure records a known Radon limitation: it returns zero Halstead values for functions that contain `try/except`.

## How the risk score works

```
score = 0.35 x smell count factor
      + 0.25 x model probability
      + 0.25 x maintainability factor
      + 0.15 x complexity factor
```

Each factor is scaled to 0-1. The weights and the 0.33 and 0.66 thresholds were chosen by hand and have not been validated.

The quality gate fails if any file is HIGH, if more than 50% of files are MEDIUM or HIGH, or if the average score is above 0.5.

## Models

Logistic Regression and Random Forest were trained and compared on the Python Code Smell Datasets (Sandouka and Aljamaan, 2023, https://doi.org/10.5281/zenodo.7512516), which are in `data/raw/`. Random Forest scored best in 5-fold stratified cross-validation:

| Dataset | Logistic Regression F1 | Random Forest F1 |
|---|---|---|
| Large Class | 0.771 | 0.839 |
| Long Method | 0.856 | 0.920 |

To rerun the comparison: `python3 -m src.ml.cross_validate`. To retrain the saved models: `python3 -m src.ml.train` (this overwrites `src/ml/saved_models/`).

## Project structure

```
src/analyzer/   parser, metrics, smell detectors, analyzer
src/ml/         training, cross-validation, risk score, quality gate, saved models
src/app/        Flask dashboard and charts
src/pipeline.py          one function that runs everything
src/recommendations.py   refactoring advice
tests/          pytest tests
data/raw/       training datasets
sample_projects/   clean and messy example code
```

## Limitations

- The models detect only two size-based smells, and size features (SLOC, LOC, LLOC) drive most of their decisions.
- All training data comes from four libraries (SciPy, Matplotlib, Django, NumPy), so behaviour on unseen code is untested.
- The score estimates how likely smells are now. It does not forecast future problems.
- The weights, thresholds and detector rules have not been validated against labelled data.
- The dashboard uses Flask's development server and has no authentication, so it is for local use only.

## Status

Work in progress. Evaluation on real open-source repositories and the comparison with SonarQube are not done yet.