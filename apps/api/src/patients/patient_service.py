from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from patients.embedding_worker import process_record_embeddings
from patients.models import MedicalRecord, Patient, Prescription, RecordType
from patients.storage_service import StorageService


class PatientCreate(BaseModel):
    full_name: str
    date_of_birth: date
    sex: str
    contact_email: str
    contact_phone: str
    blood_group: str | None = None
    allergies: list[str] = Field(default_factory=list)


class PrescriptionCreate(BaseModel):
    prescribed_by: str
    prescribed_at: datetime
    medications: list[dict[str, str]]
    notes: str | None = None


class PatientService:
    def __init__(self, db: Session, storage: Any = None) -> None:
        self.db = db
        self.storage: StorageService | Any = storage or StorageService()

    def create_patient(self, data: PatientCreate) -> Patient:
        row = Patient(**data.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_patient(self, patient_id: UUID) -> Patient | None:
        return self.db.get(Patient, str(patient_id))

    async def upload_record(
        self,
        patient_id: UUID,
        file: UploadFile,
        record_type: RecordType,
        notes: str | None,
        background_tasks: BackgroundTasks,
    ) -> MedicalRecord:
        object_key = await self.storage.upload_file(patient_id=patient_id, file=file, record_type=record_type)
        url = self.storage.get_presigned_url(object_key)
        row = MedicalRecord(
            patient_id=str(patient_id),
            record_type=record_type,
            file_name=file.filename or "upload.bin",
            file_path=object_key,
            file_url=url,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_at=datetime.now(timezone.utc),
            notes=notes,
            is_processed=False,
            embedding_id=None,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        background_tasks.add_task(process_record_embeddings, row.id, self.db)
        return row

    def get_patient_records(self, patient_id: UUID, limit: int = 50, offset: int = 0) -> list[MedicalRecord]:
        stmt = (
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == str(patient_id))
            .order_by(MedicalRecord.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = list(self.db.execute(stmt).scalars().all())
        for row in rows:
            row.file_url = self.storage.get_presigned_url(row.file_path)
        return rows

    def get_record(self, patient_id: UUID, record_id: UUID) -> MedicalRecord | None:
        row = self.db.get(MedicalRecord, str(record_id))
        if row is None or row.patient_id != str(patient_id):
            return None
        row.file_url = self.storage.get_presigned_url(row.file_path)
        return row

    def delete_record(self, patient_id: UUID, record_id: UUID) -> bool:
        row = self.db.get(MedicalRecord, str(record_id))
        if row is None or row.patient_id != str(patient_id):
            return False
        _ = self.storage.delete_file(row.file_path)
        self.db.delete(row)
        self.db.commit()
        return True

    def add_prescription(self, patient_id: UUID, data: PrescriptionCreate) -> Prescription:
        row = Prescription(patient_id=str(patient_id), **data.model_dump())
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_prescriptions(self, patient_id: UUID, limit: int = 50, offset: int = 0) -> list[Prescription]:
        stmt = (
            select(Prescription)
            .where(Prescription.patient_id == str(patient_id))
            .order_by(Prescription.prescribed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

