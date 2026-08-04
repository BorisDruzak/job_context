from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_brief_and_plan_capture_current_operator_progress() -> None:
    status = yaml.safe_load(
        (ROOT / "data/sosnovsky/current-status.yaml").read_text(encoding="utf-8")
    )
    progress = status["operator_progress"]

    assert progress["pos"]["site_widget_audit_completed"] is True
    assert progress["pos"]["audit_reflected_in_official_rating"] is False
    assert progress["pos"]["territorial_administrations_without_sites"] == 4
    assert progress["pos"]["widget_setup_completed"] is False

    assert progress["gov_publics"]["all_groups_formatted"] is True
    assert progress["gov_publics"]["autoposting_configured"] is True
    assert progress["stray_animals"]["information_communicated_to_staff"] is True
    assert progress["urban_environment"]["max_resident_outreach_active"] is True
    assert progress["urban_environment"]["online_meetings_work_active"] is True
    assert progress["urban_environment"]["workload_constraint"] == "high"

    brief = (ROOT / "reports/sosnovsky-2026-06-brief.md").read_text(encoding="utf-8")
    plan = (ROOT / "docs/plans/rating-improvement-plan-2026.md").read_text(encoding="utf-8")
    assert "4 территориальных управлений" in brief
    assert "проверка всех виджетов" in brief.lower()
    assert "не отражена в официальном рейтинге" in brief.lower()
    assert "автопостинг" in brief.lower()
    assert "с сентября" in brief.lower()
    assert "4 территориальных управлений" in plan
    assert "назначить владельцев показателей 12–14" in plan
