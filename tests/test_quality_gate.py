"""Tests for the project-level quality gate."""

import pytest

from src.ml.quality_gate import evaluate_quality_gate


def file(label, score):
    """A minimal per-file result, as compute_risk() would produce."""
    return {"risk_label": label, "composite_score": score}


def test_all_low_files_pass():
    result = evaluate_quality_gate([file("LOW", 0.1), file("LOW", 0.2)])
    assert result["status"] == "PASS"
    assert result["reasons"] == []


def test_a_single_high_file_fails():
    files = [file("LOW", 0.1)] * 9 + [file("HIGH", 0.7)]
    result = evaluate_quality_gate(files)
    assert result["status"] == "FAIL"
    assert len(result["reasons"]) == 1
    assert "HIGH" in result["reasons"][0]


def test_too_many_elevated_files_fail():
    result = evaluate_quality_gate([file("MEDIUM", 0.4)] * 3)
    assert result["status"] == "FAIL"
    assert len(result["reasons"]) == 1
    assert "MEDIUM or HIGH" in result["reasons"][0]


def test_high_average_score_fails():
    # Labels are set directly so that only the average-score rule is triggered.
    result = evaluate_quality_gate([file("LOW", 0.9), file("LOW", 0.9)])
    assert result["status"] == "FAIL"
    assert len(result["reasons"]) == 1
    assert "Average" in result["reasons"][0]


def test_exactly_half_elevated_still_passes():
    result = evaluate_quality_gate([file("LOW", 0.1), file("MEDIUM", 0.4)])
    assert result["status"] == "PASS"


def test_average_exactly_at_limit_still_passes():
    result = evaluate_quality_gate([file("LOW", 0.5), file("LOW", 0.5)])
    assert result["status"] == "PASS"


def test_empty_project_fails():
    result = evaluate_quality_gate([])
    assert result["status"] == "FAIL"
    assert result["total_files"] == 0
    assert result["reasons"] == ["No files were analysed."]


def test_counts_and_average_are_reported():
    result = evaluate_quality_gate(
        [file("HIGH", 0.7), file("MEDIUM", 0.5), file("LOW", 0.1)]
    )
    assert (result["high"], result["medium"], result["low"]) == (1, 1, 1)
    assert result["total_files"] == 3
    assert result["average_score"] == pytest.approx(0.433, abs=0.001)