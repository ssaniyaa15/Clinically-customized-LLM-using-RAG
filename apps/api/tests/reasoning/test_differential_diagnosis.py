import numpy as np
from _pytest.monkeypatch import MonkeyPatch

from reasoning.differential_diagnosis import DDxOutput, DifferentialDiagnosisHead, RetrievedChunk


def test_parse_response_ranks_descending() -> None:
    raw = (
        '{"diagnoses":['
        '{"name":"B","icd10_code":"B00","confidence":0.2,"evidence_snippets":[]},'
        '{"name":"A","icd10_code":"A00","confidence":0.8,"evidence_snippets":["x"]}'
        "]}"
    )
    out = DifferentialDiagnosisHead._parse_response(raw)
    assert out.diagnoses[0].name == "A"
    assert out.diagnoses[1].name == "B"


def test_build_prompt_contains_context() -> None:
    prompt = DifferentialDiagnosisHead._build_prompt(
        "query", [RetrievedChunk(text="ctx1", score=0.1), RetrievedChunk(text="ctx2", score=0.2)]
    )
    assert "ctx1" in prompt and "ctx2" in prompt


def test_run_with_mocked_llm(monkeypatch: MonkeyPatch) -> None:
    head = DifferentialDiagnosisHead()
    monkeypatch.setattr(head, "_embed_query", lambda q: np.ones((768,), dtype=np.float32))
    monkeypatch.setattr(head, "_retrieve", lambda emb, top_k=5: [RetrievedChunk(text="evidence", score=0.1)])
    monkeypatch.setattr(
        head,
        "_call_llm",
        lambda prompt: '{"diagnoses":[{"name":"Pneumonia","icd10_code":"J18.9","confidence":0.9,'
        '"evidence_snippets":["CXR infiltrates"]}]}',
    )
    out = head.run("shortness of breath")
    assert isinstance(out, DDxOutput)
    assert out.diagnoses[0].icd10_code == "J18.9"

