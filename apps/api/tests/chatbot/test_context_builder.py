from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from _pytest.monkeypatch import MonkeyPatch
from patients.database import Base, SessionLocal, engine
from patients.models import Patient, Prescription
from chatbot.context_builder import build_patient_context


def test_build_patient_context_with_mocked_faiss(monkeypatch: MonkeyPatch) -> None:
    Base.metadata.create_all(engine)
    patient_id = str(uuid4())
    with SessionLocal() as db:
        db.add(
            Patient(
                id=patient_id,
                full_name="Alice",
                date_of_birth=date(1991, 1, 1),
                sex="F",
                contact_email="a@x.com",
                contact_phone="123",
                blood_group="O+",
                allergies=["penicillin"],
            )
        )
        db.add(
            Prescription(
                patient_id=patient_id,
                prescribed_by="Dr A",
                prescribed_at=datetime.now(timezone.utc),
                medications=[{"name": "DrugA", "dose": "10mg", "frequency": "BID", "duration": "5d"}],
                notes=None,
            )
        )
        db.commit()
    monkeypatch.setattr(
        "chatbot.context_builder._retrieve_relevant_chunks",
        lambda pid, q, top_k=5: ["chunk 1", "chunk 2"],
    )
    import asyncio

    out = asyncio.run(build_patient_context(UUID(patient_id), "headache"))
    assert "PATIENT PROFILE:" in out
    assert "chunk 1" in out
    assert "DrugA" in out

