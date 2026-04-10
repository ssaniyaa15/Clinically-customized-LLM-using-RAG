from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    date_of_birth: date
    sex: str
    contact_email: str
    contact_phone: str
    blood_group: str | None
    allergies: list[str]
    created_at: datetime
    updated_at: datetime


class MedicalRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    record_type: str
    file_name: str
    file_path: str
    file_url: str
    mime_type: str
    uploaded_at: datetime
    notes: str | None
    is_processed: bool
    embedding_id: str | None


class PrescriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    patient_id: str
    prescribed_by: str
    prescribed_at: datetime
    medications: list[dict[str, str]] = Field(default_factory=list)
    notes: str | None

