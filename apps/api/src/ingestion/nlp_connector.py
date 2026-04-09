from __future__ import annotations

from pydantic import BaseModel


class ClinicalTextPayload(BaseModel):
    note_type: str
    raw_text: str
    char_count: int
    language: str


class NLPConnector:
    @staticmethod
    def ingest_note(
        raw_text: str, note_type: str | None = None, language: str = "en"
    ) -> ClinicalTextPayload:
        inferred_type = note_type or NLPConnector._infer_note_type(raw_text)
        return ClinicalTextPayload(
            note_type=inferred_type,
            raw_text=raw_text,
            char_count=len(raw_text),
            language=language,
        )

    @staticmethod
    def _infer_note_type(raw_text: str) -> str:
        text = raw_text.lower()
        if "impression" in text or "findings" in text:
            return "radiology"
        if "rx" in text or "prescription" in text or "dose" in text:
            return "prescription"
        return "physician"

