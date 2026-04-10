from _pytest.monkeypatch import MonkeyPatch

from output.alert_service import rank_alert, summarise_recommendation
from output.integration_api import build_mock_recommendation
from safety.human_in_loop import gate_recommendation


async def _fake_llm_complete(**kwargs: object) -> object:
    class _Resp:
        content = "Brief clinical summary."

    return _Resp()


def test_summarise_recommendation_llm(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr("output.alert_service.llm_complete", _fake_llm_complete)
    rec = build_mock_recommendation("patient-001")
    summary = summarise_recommendation(rec)
    assert summary == "Brief clinical summary."


def test_rank_alert() -> None:
    gated = gate_recommendation(build_mock_recommendation("patient-001"))
    alert = rank_alert(gated)
    assert alert.level in {"info", "warning", "critical"}

