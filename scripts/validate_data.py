from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

import yaml

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,}")
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+7|8)\s*\(?\d{3}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)"
)
SECRET_RE = re.compile(
    r"(?i)(?:password|passwd|token|api[_-]?key|secret)\s*[:=]\s*[^\s]+"
)
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".csv", ".py", ".txt"}
EXPECTED_SOURCE_IDS = {
    "methodology-2025-order-147",
    "methodology-2026-order-61",
    "rating-2026-04",
    "rating-2026-05",
    "rating-2026-06",
    "subcommission-34-2026-08-03",
    "operator-context-2026-08-04",
}


def scan_public_text(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for kind, pattern in (("email", EMAIL_RE), ("phone", PHONE_RE), ("secret", SECRET_RE)):
        for match in pattern.finditer(text):
            findings.append({"kind": kind, "value": match.group(0)})
    return findings


def _load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_repository(root: Path) -> list[str]:
    errors: list[str] = []

    manifest_path = root / "data/sources/manifest.yaml"
    if not manifest_path.exists():
        errors.append("missing data/sources/manifest.yaml")
        return errors
    manifest = _load_yaml(manifest_path)
    sources = manifest.get("sources", []) if isinstance(manifest, dict) else []
    source_ids = [item.get("id") for item in sources if isinstance(item, dict)]
    if len(source_ids) != len(set(source_ids)):
        errors.append("source IDs are not unique")
    missing_sources = EXPECTED_SOURCE_IDS - set(source_ids)
    if missing_sources:
        errors.append(f"missing required source IDs: {sorted(missing_sources)}")

    for year, count in ((2025, 10), (2026, 14)):
        path = root / f"data/methodology/indicators-{year}.yaml"
        if not path.exists():
            errors.append(f"missing {path.relative_to(root)}")
            continue
        data = _load_yaml(path)
        indicators = data.get("indicators", [])
        codes = [item.get("code") for item in indicators]
        if len(indicators) != count:
            errors.append(f"{path.relative_to(root)}: expected {count} indicators")
        if len(codes) != len(set(codes)):
            errors.append(f"{path.relative_to(root)}: indicator codes are not unique")
        weights = [float(item.get("base_weight", 0)) for item in indicators]
        if abs(sum(weights) - 1.0) > 1e-9:
            errors.append(f"{path.relative_to(root)}: base weights do not sum to 1")

    for period in ("2026-04", "2026-05", "2026-06"):
        path = root / f"data/ratings/{period}-overall.csv"
        if not path.exists():
            errors.append(f"missing {path.relative_to(root)}")
            continue
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if len(rows) != 43:
            errors.append(f"{path.relative_to(root)}: expected 43 rows, got {len(rows)}")
        municipalities = [row.get("municipality") for row in rows]
        if len(municipalities) != len(set(municipalities)):
            errors.append(f"{path.relative_to(root)}: municipalities are not unique")
        ranks = sorted(int(row["rank"]) for row in rows)
        if ranks != list(range(1, 44)):
            errors.append(f"{path.relative_to(root)}: ranks must be 1..43")
        if {row.get("source_id") for row in rows} != {f"rating-{period}"}:
            errors.append(f"{path.relative_to(root)}: invalid source_id")

    responsibility_path = root / "data/sosnovsky/indicator-responsibility.yaml"
    if responsibility_path.exists():
        responsibility = _load_yaml(responsibility_path)
        codes = [item.get("indicator_code") for item in responsibility.get("indicators", [])]
        expected = {
            item["code"]
            for item in _load_yaml(root / "data/methodology/indicators-2026.yaml")["indicators"]
        }
        if set(codes) != expected:
            errors.append("indicator responsibility does not cover all 2026 indicators")

    assignments_path = root / "data/sosnovsky/assignments.yaml"
    if assignments_path.exists():
        assignments = _load_yaml(assignments_path).get("assignments", [])
        ids = [item.get("id") for item in assignments]
        if len(ids) != len(set(ids)):
            errors.append("assignment IDs are not unique")

    for code, filename in (
        ("mszu", "01-mszu.md"), ("pos", "02-pos.md"),
        ("gov_publics", "03-gov-publics.md"), ("goskey", "04-goskey.md"),
        ("transport", "05-transport.md"), ("urban_environment", "06-urban-environment.md"),
        ("gisogd", "07-gisogd.md"), ("education", "08-education.md"),
        ("sport", "09-sport.md"), ("stray_animals", "10-stray-animals.md"),
        ("broadband", "11-broadband.md"), ("ai_datasets", "12-ai-datasets.md"),
        ("centralized_ai", "13-centralized-ai.md"), ("local_ai", "14-local-ai.md"),
    ):
        if not (root / "docs/indicators" / filename).exists():
            errors.append(f"missing indicator document for {code}")

    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for finding in scan_public_text(text):
            # Regex examples in validator tests/source are not operational contact data.
            if path.parts[-2:] in [("scripts", "validate_data.py"), ("tests", "test_data_contracts.py")]:
                continue
            errors.append(f"{path.relative_to(root)}: contains {finding['kind']}")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
