from ingestion.nlp_connector import NLPConnector


def test_ingest_note_with_inferred_type() -> None:
    payload = NLPConnector.ingest_note("Findings: mild bilateral opacities.")
    assert payload.note_type == "radiology"
    assert payload.char_count == len(payload.raw_text)
    assert payload.language == "en"


def test_ingest_note_with_explicit_type() -> None:
    payload = NLPConnector.ingest_note("Take 2 tablets daily", note_type="prescription", language="en")
    assert payload.note_type == "prescription"

