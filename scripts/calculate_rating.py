from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable

INDICATOR_FIELDS = (
    "mszu",
    "pos",
    "gov_publics",
    "goskey",
    "transport",
    "urban_environment",
    "gisogd",
    "education",
    "sport",
    "stray_animals",
    "broadband",
    "ai_datasets",
    "centralized_ai",
    "local_ai",
)


def redistribute_weights(
    weights: dict[str, float], values: dict[str, float | None]
) -> dict[str, float]:
    """Return normalized weights for indicators with non-null values."""
    unknown = set(values) - set(weights)
    if unknown:
        raise ValueError(f"values contain indicators without weights: {sorted(unknown)}")
    applicable = {
        code: float(weight)
        for code, weight in weights.items()
        if values.get(code) is not None
    }
    total = sum(applicable.values())
    if total <= 0:
        raise ValueError("at least one indicator must be applicable")
    return {code: weight / total for code, weight in applicable.items()}


def calculate_score(
    weights: dict[str, float], values: dict[str, float | None]
) -> float:
    effective = redistribute_weights(weights, values)
    return sum(float(values[code]) * weight for code, weight in effective.items())


def classify_score(score: float) -> str:
    if score >= 85.0:
        return "leader"
    if score >= 70.0:
        return "intermediate"
    return "lagging"


def compare_with_official(
    calculated: float, official: float, tolerance: float = 0.02
) -> dict[str, float | bool]:
    delta = calculated - official
    return {
        "calculated": calculated,
        "official": official,
        "delta": delta,
        "matches": abs(delta) <= tolerance,
    }


def parse_rating_values(row: dict[str, str]) -> dict[str, float | None]:
    return {
        code: (float(row[code]) if row.get(code, "") != "" else None)
        for code in INDICATOR_FIELDS
        if code in row
    }


def equal_weights(codes: Iterable[str]) -> dict[str, float]:
    codes = tuple(codes)
    if not codes:
        raise ValueError("at least one code is required")
    weight = 1.0 / len(codes)
    return {code: weight for code in codes}


def verify_rating_csv(path: Path, tolerance: float = 0.02) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            values = parse_rating_values(row)
            weights = equal_weights(values.keys())
            calculated = calculate_score(weights, values)
            official = float(row["official_total"])
            comparison = compare_with_official(calculated, official, tolerance)
            if not comparison["matches"]:
                findings.append(
                    {
                        "municipality": row["municipality"],
                        "period": row["period"],
                        **comparison,
                    }
                )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify municipal rating CSV totals")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.02)
    args = parser.parse_args()
    findings = verify_rating_csv(args.csv_path, args.tolerance)
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
