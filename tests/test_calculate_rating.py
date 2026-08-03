from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.calculate_rating import (
    calculate_score,
    classify_score,
    compare_with_official,
    equal_weights,
    parse_rating_values,
    redistribute_weights,
    verify_rating_csv,
)

ROOT = Path(__file__).resolve().parents[1]


def test_redistributes_missing_equal_weight_indicator() -> None:
    weights = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
    values = {"a": 100.0, "b": 50.0, "c": None, "d": 0.0}
    actual = redistribute_weights(weights, values)
    assert actual == pytest.approx({"a": 1 / 3, "b": 1 / 3, "d": 1 / 3})
    assert calculate_score(weights, values) == pytest.approx(50.0)


def test_rejects_unknown_weight_code() -> None:
    with pytest.raises(ValueError, match="without weights"):
        redistribute_weights({"a": 1.0}, {"a": 10.0, "b": 20.0})


def test_classifies_official_groups() -> None:
    assert classify_score(85.0) == "leader"
    assert classify_score(70.0) == "intermediate"
    assert classify_score(69.999) == "lagging"


def test_compare_uses_rounding_tolerance() -> None:
    result = compare_with_official(79.795, 79.80)
    assert result["matches"] is True


@pytest.mark.parametrize("period", ["2026-04", "2026-05", "2026-06"])
def test_full_rating_export_reproduces_official_totals(period: str) -> None:
    assert verify_rating_csv(ROOT / f"data/ratings/{period}-overall.csv") == []


def test_sosnovsky_june_calculation() -> None:
    with (ROOT / "data/ratings/2026-06-overall.csv").open(encoding="utf-8", newline="") as handle:
        row = next(item for item in csv.DictReader(handle) if item["municipality"] == "Сосновский МО")
    values = parse_rating_values(row)
    score = calculate_score(equal_weights(values.keys()), values)
    assert score == pytest.approx(79.80, abs=0.01)
