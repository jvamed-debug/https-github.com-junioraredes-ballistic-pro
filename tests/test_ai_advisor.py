"""Tests for the AI advisor service (offline mode)."""

import sys
from contextlib import contextmanager
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

from services.ai_advisor import (
    AdvisorResponse,
    AnthropicAdvisor,
    BALLISTIC_SYSTEM_PROMPT,
    BallisticAdvisor,
    OpenAIAdvisor,
)


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


@contextmanager
def _fake_sdk(module_name, class_name, client):
    """Stand in for an LLM SDK.

    Both adapters import their SDK inside the method, so putting a module in
    sys.modules is enough to intercept it — and keeps these tests off the
    network whether or not the real package happens to be installed.
    """
    module = ModuleType(module_name)
    setattr(module, class_name, MagicMock(return_value=client))
    with patch.dict(sys.modules, {module_name: module}):
        yield SimpleNamespace(client=client)


def _sdk_that_fails(module_name, class_name, message):
    client = MagicMock()
    client.messages.create.side_effect = RuntimeError(message)
    client.chat.completions.create.side_effect = RuntimeError(message)
    return _fake_sdk(module_name, class_name, client)


def _sdk_that_works(module_name, class_name):
    client = MagicMock()
    client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(text="resposta")]
    )
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="resposta"))]
    )
    return _fake_sdk(module_name, class_name, client)


class TestConfigure:
    def test_unknown_provider_is_rejected(self):
        adv = BallisticAdvisor()
        assert adv.configure("gemini", "chave") is False
        assert not adv.is_configured

    def test_failing_health_check_leaves_advisor_unconfigured(self):
        """A provider that cannot answer must not be adopted. It used to be
        assigned before the health check, so a bad key left is_configured True
        and every later analysis returned the SDK's error string dressed up as
        a ballistic report — bypassing the offline mode that still works."""
        adv = BallisticAdvisor()
        with patch.object(AnthropicAdvisor, "health_check", return_value=False):
            assert adv.configure("anthropic", "chave-ruim") is False
        assert not adv.is_configured

    def test_analysis_falls_back_offline_after_failed_configure(self):
        adv = BallisticAdvisor()
        with patch.object(OpenAIAdvisor, "health_check", return_value=False):
            adv.configure("openai", "chave-ruim")
        result = adv.analyze_grouping([{"id": 1, "group_size_mm": 20.0, "shots": [(0, 0)]}])
        assert result.provider == "offline"
        assert "[Erro" not in result.content

    def test_healthy_provider_is_adopted(self):
        adv = BallisticAdvisor()
        with patch.object(AnthropicAdvisor, "health_check", return_value=True):
            assert adv.configure("anthropic", "chave-boa") is True
        assert adv.is_configured

    def test_failed_reconfigure_keeps_the_working_provider(self):
        adv = BallisticAdvisor()
        with patch.object(AnthropicAdvisor, "health_check", return_value=True):
            adv.configure("anthropic", "chave-boa")
        with patch.object(OpenAIAdvisor, "health_check", return_value=False):
            adv.configure("openai", "chave-ruim")
        assert adv.is_configured
        with patch.object(AnthropicAdvisor, "complete", return_value="laudo"):
            assert adv.analyze_grouping([]).provider == "anthropic"


class TestOnlineDelegation:
    """With a provider configured, the three analyses must reach it and carry
    the safety-constrained system prompt."""

    def _configured(self):
        adv = BallisticAdvisor()
        with patch.object(AnthropicAdvisor, "health_check", return_value=True):
            adv.configure("anthropic", "chave")
        return adv

    def test_grouping_sends_data_and_returns_provider_content(self):
        adv = self._configured()
        with patch.object(AnthropicAdvisor, "complete", return_value="laudo do modelo") as m:
            res = adv.analyze_grouping([{"id": 1, "group_size_mm": 31.5}])
        assert res.content == "laudo do modelo"
        assert res.provider == "anthropic"
        system, user = m.call_args[0]
        assert system == BALLISTIC_SYSTEM_PROMPT
        assert "31.5" in user

    def test_load_suggestion_includes_every_input(self):
        adv = self._configured()
        with patch.object(AnthropicAdvisor, "complete", return_value="ok") as m:
            adv.suggest_load(
                ".308 Winchester", "Sierra 168gr", "IMR 4064",
                {"charge": 42.5, "velocity": 2650, "sd": 8, "grouping": 22},
            )
        user = m.call_args[0][1]
        for expected in (".308 Winchester", "Sierra 168gr", "IMR 4064", "42.5", "2650", "8", "22"):
            assert expected in user, expected

    def test_missing_load_fields_render_as_na(self):
        adv = self._configured()
        with patch.object(AnthropicAdvisor, "complete", return_value="ok") as m:
            adv.suggest_load(".223", "55gr", "H335", {})
        assert "N/A" in m.call_args[0][1]

    def test_trend_analysis_serialises_sessions(self):
        adv = self._configured()
        sessions = [{"velocity_avg": 2700, "grouping_mm": 30}]
        with patch.object(AnthropicAdvisor, "complete", return_value="ok") as m:
            res = adv.analyze_performance_trend(sessions)
        assert res.provider == "anthropic"
        assert "2700" in m.call_args[0][1]

    def test_accented_data_is_not_escaped_into_unicode_sequences(self):
        """ensure_ascii=False keeps the prompt readable for a pt-BR model."""
        adv = self._configured()
        with patch.object(AnthropicAdvisor, "complete", return_value="ok") as m:
            adv.analyze_grouping([{"id": 1, "obs": "munição"}])
        assert "munição" in m.call_args[0][1]


class TestProviderAdapters:
    def test_anthropic_reports_its_name(self):
        assert AnthropicAdvisor("k").provider_name == "anthropic"

    def test_openai_reports_its_name(self):
        assert OpenAIAdvisor("k").provider_name == "openai"

    def test_anthropic_complete_returns_error_string_instead_of_raising(self):
        """The tab renders whatever comes back, so a transport failure has to
        arrive as text rather than an exception."""
        with _sdk_that_fails("anthropic", "Anthropic", "sem rede"):
            out = AnthropicAdvisor("chave").complete("sys", "user")
        assert out == "[Erro Anthropic] sem rede"

    def test_openai_complete_returns_error_string_instead_of_raising(self):
        with _sdk_that_fails("openai", "OpenAI", "401 unauthorized"):
            out = OpenAIAdvisor("chave").complete("sys", "user")
        assert out == "[Erro OpenAI] 401 unauthorized"

    def test_health_check_is_false_when_the_sdk_cannot_answer(self):
        with _sdk_that_fails("anthropic", "Anthropic", "boom"):
            assert AnthropicAdvisor("chave").health_check() is False
        with _sdk_that_fails("openai", "OpenAI", "boom"):
            assert OpenAIAdvisor("chave").health_check() is False

    def test_health_check_is_true_when_the_sdk_answers(self):
        with _sdk_that_works("anthropic", "Anthropic"):
            assert AnthropicAdvisor("chave").health_check() is True
        with _sdk_that_works("openai", "OpenAI"):
            assert OpenAIAdvisor("chave").health_check() is True

    def test_anthropic_returns_empty_string_for_an_empty_completion(self):
        with _sdk_that_works("anthropic", "Anthropic") as sdk:
            sdk.client.messages.create.return_value = SimpleNamespace(content=[])
            assert AnthropicAdvisor("chave").complete("sys", "user") == ""

    def test_openai_returns_empty_string_when_content_is_none(self):
        with _sdk_that_works("openai", "OpenAI") as sdk:
            sdk.client.chat.completions.create.return_value = SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=None))]
            )
            assert OpenAIAdvisor("chave").complete("sys", "user") == ""


class TestOfflineGrouping:
    def test_rating_thresholds(self):
        adv = BallisticAdvisor()
        cases = [(10.0, "EXCELENTE"), (24.9, "EXCELENTE"), (25.0, "BOM"),
                 (49.9, "BOM"), (50.0, "REGULAR"), (79.9, "REGULAR"),
                 (80.0, "NECESSITA MELHORIA")]
        for size, expected in cases:
            content = adv.analyze_grouping([{"id": 1, "group_size_mm": size}]).content
            assert expected in content, f"{size}mm deveria ser {expected}"

    def test_shot_count_falls_back_to_length_of_shots(self):
        adv = BallisticAdvisor()
        content = adv.analyze_grouping(
            [{"id": 1, "group_size_mm": 20.0, "shots": [(0, 0), (1, 1), (2, 2)]}]
        ).content
        assert "3 impactos" in content

    def test_empty_groups_still_returns_a_response(self):
        adv = BallisticAdvisor()
        res = adv.analyze_grouping([])
        assert res.provider == "offline"
        assert res.confidence == "low"


class TestOfflineLoadSuggestion:
    def _content(self, **data):
        return BallisticAdvisor().suggest_load(".308", "168gr", "Varget", data).content

    def test_sd_bands(self):
        assert "EXCELENTE consistencia" in self._content(sd=8)
        assert "BOM, aceitavel" in self._content(sd=15)
        assert "REGULAR" in self._content(sd=25)
        assert "ELEVADO" in self._content(sd=40)

    def test_grouping_bands(self):
        assert "EXCELENTE" in self._content(grouping=20)
        assert "BOM para uso tatico" in self._content(grouping=40)
        assert "revisar tecnica" in self._content(grouping=70)

    def test_no_measurements_asks_for_a_chronograph(self):
        assert "Dados insuficientes" in self._content()

    def test_always_carries_the_minimum_charge_warning(self):
        """Load advice without this line could get someone hurt."""
        for data in ({}, {"sd": 8}, {"charge": 42.0, "velocity": 2700, "sd": 9, "grouping": 20}):
            assert "carga minima" in self._content(**data)

    def test_reports_charge_and_velocity_when_given(self):
        content = self._content(charge=42.5, velocity=2650)
        assert "42.5 grains" in content
        assert "2650 fps" in content


class TestOfflineTrend:
    def _content(self, sessions):
        return BallisticAdvisor().analyze_performance_trend(sessions).content

    def test_single_session_asks_for_more(self):
        assert "Registre mais sessoes" in self._content([{"velocity_avg": 2700}])

    def test_counts_sessions(self):
        assert "3" in self._content([{"velocity_avg": 2700}] * 3)

    def test_velocity_trend_stable_rising_falling(self):
        def sessions(vals):
            return [{"velocity_avg": v} for v in vals]
        assert "ESTAVEL" in self._content(sessions([2700, 2701, 2702, 2703, 2704, 2705]))
        assert "SUBINDO" in self._content(sessions([2600, 2600, 2600, 2700, 2700, 2700]))
        assert "DESCENDO" in self._content(sessions([2700, 2700, 2700, 2600, 2600, 2600]))

    def test_accepts_both_key_spellings(self):
        """Sessions reach this from two callers using different field names."""
        a = self._content([{"velocity_avg": 2700}, {"velocity_avg": 2700}])
        b = self._content([{"velocity": 2700}, {"velocity": 2700}])
        assert "2700 fps" in a
        assert "2700 fps" in b

    def test_sd_consistency_verdict(self):
        assert "Consistencia: BOA" in self._content([{"velocity_sd": 9}, {"velocity_sd": 10}])
        assert "IRREGULAR" in self._content([{"velocity_sd": 25}, {"velocity_sd": 30}])

    def test_precision_direction(self):
        def sessions(vals):
            return [{"grouping_mm": g} for g in vals]
        assert "MELHORANDO" in self._content(sessions([50, 50, 50, 20, 20, 20]))
        assert "PIORANDO" in self._content(sessions([20, 20, 20, 50, 50, 50]))
        assert "Precisao: ESTAVEL" in self._content(sessions([30, 30, 30, 30, 30, 30]))
