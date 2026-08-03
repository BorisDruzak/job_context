from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest
import yaml

from scripts.validate_data import scan_public_text, validate_repository

ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_source_manifest_has_unique_required_ids() -> None:
    data = yaml.safe_load((ROOT / "data/sources/manifest.yaml").read_text(encoding="utf-8"))
    sources = data["sources"]
    ids = [item["id"] for item in sources]
    assert len(ids) == len(set(ids))
    assert {
        "methodology-2025-order-147",
        "methodology-2026-order-61",
        "rating-2026-04",
        "rating-2026-05",
        "rating-2026-06",
        "subcommission-34-2026-08-03",
        "operator-context-2026-08-04",
    } <= set(ids)


@pytest.mark.parametrize(
    ("path", "expected_count", "expected_weight"),
    [
        ("data/methodology/indicators-2025.yaml", 10, 0.1),
        ("data/methodology/indicators-2026.yaml", 14, 1 / 14),
    ],
)
def test_methodology_indicator_contract(path: str, expected_count: int, expected_weight: float) -> None:
    data = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    indicators = data["indicators"]
    assert len(indicators) == expected_count
    assert len({item["code"] for item in indicators}) == expected_count
    assert all(abs(float(item["base_weight"]) - expected_weight) < 1e-9 for item in indicators)
    assert abs(sum(float(item["base_weight"]) for item in indicators) - 1.0) < 1e-9


def test_responsibility_covers_every_2026_indicator() -> None:
    methodology = yaml.safe_load((ROOT / "data/methodology/indicators-2026.yaml").read_text(encoding="utf-8"))
    responsibility = yaml.safe_load((ROOT / "data/sosnovsky/indicator-responsibility.yaml").read_text(encoding="utf-8"))
    expected = {item["code"] for item in methodology["indicators"]}
    actual = {item["indicator_code"] for item in responsibility["indicators"]}
    assert actual == expected


@pytest.mark.parametrize("period", ["2026-04", "2026-05", "2026-06"])
def test_overall_rating_has_43_unique_municipalities(period: str) -> None:
    rows = read_csv(f"data/ratings/{period}-overall.csv")
    assert len(rows) == 43
    assert len({row["municipality"] for row in rows}) == 43
    assert sorted(int(row["rank"]) for row in rows) == list(range(1, 44))
    assert {row["period"] for row in rows} == {period}


def test_sosnovsky_history_matches_official_exports() -> None:
    rows = read_csv("data/ratings/sosnovsky-history.csv")
    actual = [(row["period"], int(row["rank"]), float(row["official_total"])) for row in rows]
    assert actual == [
        ("2026-04", 30, 70.75),
        ("2026-05", 33, 69.59),
        ("2026-06", 29, 79.80),
    ]


def test_assignments_are_unique_and_contact_free() -> None:
    data = yaml.safe_load((ROOT / "data/sosnovsky/assignments.yaml").read_text(encoding="utf-8"))
    ids = [item["id"] for item in data["assignments"]]
    assert len(ids) == len(set(ids))
    text = (ROOT / "docs/assignments/subcommission-34-2026-08-03.md").read_text(encoding="utf-8")
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,}", text)
    assert not re.search(r"(?:\+7|8)\s*\(?\d{3}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}", text)


def test_public_text_scanner_detects_contacts() -> None:
    findings = scan_public_text("Позвонить +7 (351) 111-22-33 или user@example.org")
    assert {item["kind"] for item in findings} == {"email", "phone"}


def test_repository_public_files_have_no_contacts_or_contract_errors() -> None:
    assert validate_repository(ROOT) == []
