"""Tests for the AI advisor service (offline mode)."""

from services.ai_advisor import BallisticAdvisor, AdvisorResponse


def test_advisor_starts_unconfigured():
    adv = BallisticAdvisor()
    assert not adv.is_configured


def test_offline_grouping_analysis():
    adv = BallisticAdvisor()
    groups = [
        {"id": 1, "group_size_mm": 20.0, "shots": [(0, 0), (1, 1)], "poi_mm": (0.5, -0.3)},
        {"id": 2, "group_size_mm": 85.0, "shots": [(100, 100)], "poi_mm": (5.0, 3.0)},
    ]
    result = adv.analyze_grouping(groups)
    assert isinstance(result, AdvisorResponse)
    assert result.provider == "offline"
    assert "EXCELENTE" in result.content
    assert "NECESSITA MELHORIA" in result.content


def test_offline_load_suggestion():
    adv = BallisticAdvisor()
    result = adv.suggest_load("9mm", "147gr FMJ", "CBC 216", {"sd": 8})
    assert isinstance(result, AdvisorResponse)
    assert result.provider == "offline"
    assert "EXCELENTE" in result.content


def test_offline_trend_analysis():
    adv = BallisticAdvisor()
    sessions = [{"data": "01/01/2025", "calibre": "9mm"}]
    result = adv.analyze_performance_trend(sessions)
    assert isinstance(result, AdvisorResponse)
    assert "1" in result.content


def test_configure_with_invalid_provider():
    adv = BallisticAdvisor()
    ok = adv.configure("invalid_provider", "fake-key")
    assert not ok


def test_offline_grouping_ratings():
    adv = BallisticAdvisor()

    groups_excellent = [{"id": 1, "group_size_mm": 15.0, "shots": [(0, 0)], "poi_mm": (0, 0)}]
    result = adv.analyze_grouping(groups_excellent)
    assert "EXCELENTE" in result.content

    groups_good = [{"id": 1, "group_size_mm": 35.0, "shots": [(0, 0)], "poi_mm": (0, 0)}]
    result = adv.analyze_grouping(groups_good)
    assert "BOM" in result.content

    groups_regular = [{"id": 1, "group_size_mm": 65.0, "shots": [(0, 0)], "poi_mm": (0, 0)}]
    result = adv.analyze_grouping(groups_regular)
    assert "REGULAR" in result.content
