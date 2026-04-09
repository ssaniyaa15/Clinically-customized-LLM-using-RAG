from _pytest.monkeypatch import MonkeyPatch

from output.alert_service import rank_alert, summarise_recommendation
from output.integration_api import build_mock_recommendation
from safety.human_in_loop import gate_recommendation


def test_summarise_recommendation_fallback(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("output.alert_service.openai_module", None)
    rec = build_mock_recommendation("patient-001")
    summary = summarise_recommendation(rec)
    assert isinstance(summary, str)
    assert len(summary) > 0


def test_rank_alert() -> None:
    gated = gate_recommendation(build_mock_recommendation("patient-001"))
    alert = rank_alert(gated)
    assert alert.level in {"info", "warning", "critical"}

