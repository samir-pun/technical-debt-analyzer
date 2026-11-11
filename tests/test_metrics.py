"""Unit tests for the metric modules: LOC, complexity, maintainability, Halstead."""

import pytest

from src.analyzer.metrics.complexity import calculate_complexity
from src.analyzer.metrics.halstead import calculate_halstead
from src.analyzer.metrics.loc import calculate_loc
from src.analyzer.metrics.maintainability import calculate_maintainability

SIMPLE = "def f(x):\n    return x\n"
BRANCHY = (
    "def f(x):\n"
    "    if x > 0:\n"
    "        if x > 10:\n"
    "            return 1\n"
    "        elif x > 5:\n"
    "            return 2\n"
    "    return 0\n"
)
BROKEN = "def f()\n    pass\n"  # missing colon, so it cannot be parsed


# --- LOC ---

def test_loc_counts_code_comment_and_blank_lines():
    result = calculate_loc("x = 1\n# a comment\n\ny = 2\n")
    assert result.total_loc == 4
    assert result.lloc == 2
    assert result.comments == 1
    assert result.blank_loc == 1


def test_loc_of_empty_source_has_no_logical_lines():
    assert calculate_loc("").lloc == 0


# --- Cyclomatic complexity ---

def test_simple_function_has_complexity_one():
    result = calculate_complexity(SIMPLE)
    assert result.max_complexity == 1
    assert result.functions[0].rank == "A"


def test_branching_raises_complexity():
    simple = calculate_complexity(SIMPLE).max_complexity
    branchy = calculate_complexity(BRANCHY).max_complexity
    assert branchy > simple


def test_source_without_functions_has_no_complexity_entries():
    result = calculate_complexity("x = 1\n")
    assert result.functions == []
    assert result.average_complexity == 0.0


def test_complexity_of_broken_source_does_not_crash():
    assert calculate_complexity(BROKEN).functions == []


# --- Maintainability index ---

def test_maintainability_score_is_between_0_and_100():
    result = calculate_maintainability(BRANCHY)
    assert 0 <= result.score <= 100
    assert result.rank in {"A", "B", "C"}


def test_maintainability_of_broken_source_is_zero():
    result = calculate_maintainability(BROKEN)
    assert result.score == 0.0
    assert result.rank == "C"


# --- Halstead ---

def test_halstead_counts_operators_and_operands():
    result = calculate_halstead("def f(a, b):\n    return a + b * 2\n")
    assert result.vocabulary > 0
    assert result.volume > 0


@pytest.mark.xfail(reason="Known Radon limitation: zero Halstead values for functions with try/except")
def test_halstead_is_nonzero_for_try_except():
    source = (
        "def f(path):\n"
        "    try:\n"
        "        return open(path).read()\n"
        "    except OSError:\n"
        "        return ''\n"
    )
    assert calculate_halstead(source).volume > 0