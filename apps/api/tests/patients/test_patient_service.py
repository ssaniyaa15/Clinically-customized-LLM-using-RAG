from __future__ import annotations

from datetime import date, datetime, timezone
from io import BytesIO
from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi import BackgroundTasks, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.datastructures import Headers

from patients.database import Base
from patients.patient_service import PatientCreate, PatientService, PrescriptionCreate


class FakeStorage:
    async def upload_file(self, patient_id: UUID, file: UploadFile, record_type: str) -> str:
        _ = (patient_id, record_type)
        _ = await file.read()
        return f"patients/{patient_id}/{record_type}/file.bin"

    def get_presigned_url(self, object_key: str, expires_hours: int = 24) -> str:
        _ = expires_hours
        return f"https://presigned.local/{object_key}"

    def delete_file(self, object_key: str) -> bool:
        _ = object_key
        return True


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    LocalSession = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    db = LocalSession()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_patient_service_create_upload_and_list(db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("patients.patient_service.process_record_embeddings", lambda record_id, db: None)
    service = PatientService(db_session, storage=FakeStorage())
    patient = service.create_patient(
        PatientCreate(
            full_name="Jane Doe",
            date_of_birth=date(1990, 1, 1),
            sex="F",
            contact_email="jane@example.com",
            contact_phone="+1000000",
            allergies=["penicillin"],
        )
    )
    assert patient.id
    file = UploadFile(
        filename="xray.png",
        file=BytesIO(b"image-bytes"),
        headers=Headers({"content-type": "image/png"}),
    )
    bg = BackgroundTasks()
    record = await service.upload_record(UUID(patient.id), file, "xray", "note", bg)
    assert record.file_url.startswith("https://presigned.local/")
    rows = service.get_patient_records(UUID(patient.id), limit=10, offset=0)
    assert len(rows) == 1
    assert rows[0].record_type == "xray"


def test_patient_service_prescriptions(db_session: Session) -> None:
    service = PatientService(db_session, storage=FakeStorage())
    patient = service.create_patient(
        PatientCreate(
            full_name="John Doe",
            date_of_birth=date(1988, 6, 2),
            sex="M",
            contact_email="john@example.com",
            contact_phone="+2000000",
            allergies=[],
        )
    )
    rx = service.add_prescription(
        UUID(patient.id),
        PrescriptionCreate(
            prescribed_by="Dr. X",
            prescribed_at=datetime.now(timezone.utc),
            medications=[{"name": "Amoxicillin", "dose": "500mg", "frequency": "BID", "duration": "7d"}],
            notes="Take with food",
        ),
    )
    assert rx.id
    rxs = service.get_prescriptions(UUID(patient.id), limit=10, offset=0)
    assert len(rxs) == 1

