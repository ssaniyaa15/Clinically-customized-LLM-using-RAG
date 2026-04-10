from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Header, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from patients.database import get_db
from patients.models import MedicalRecord, RecordType
from patients.patient_service import PatientCreate, PatientService, PrescriptionCreate
from patients.schemas import MedicalRecordRead, PatientRead, PrescriptionRead

router = APIRouter(prefix="/patients", tags=["patients"])


def _validate_patient_header(patient_id: UUID, patient_id_header: str | None) -> None:
    if patient_id_header is None:
        return
    if patient_id_header != str(patient_id):
        raise HTTPException(status_code=400, detail="patient_id header does not match path parameter")


@router.post("", response_model=PatientRead)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)) -> PatientRead:
    return PatientRead.model_validate(PatientService(db).create_patient(payload))


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    patient_id_header: str | None = Header(default=None, alias="patient_id"),
) -> PatientRead:
    _validate_patient_header(patient_id, patient_id_header)
    row = PatientService(db).get_patient(patient_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientRead.model_validate(row)


@router.post("/{patient_id}/records", response_model=MedicalRecordRead)
async def upload_record(
    patient_id: UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    record_type: RecordType = Query(...),
    notes: str | None = Query(default=None),
    db: Session = Depends(get_db),
    patient_id_header: str | None = Header(default=None, alias="patient_id"),
) -> MedicalRecordRead:
    _validate_patient_header(patient_id, patient_id_header)
    service = PatientService(db)
    if service.get_patient(patient_id) is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    row = await service.upload_record(patient_id, file, record_type, notes, background_tasks)
    return MedicalRecordRead.model_validate(row)


@router.get("/{patient_id}/records", response_model=list[MedicalRecordRead])
def list_records(
    patient_id: UUID,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    patient_id_header: str | None = Header(default=None, alias="patient_id"),
) -> list[MedicalRecordRead]:
    _validate_patient_header(patient_id, patient_id_header)
    rows = PatientService(db).get_patient_records(patient_id, limit=limit, offset=offset)
    return [MedicalRecordRead.model_validate(row) for row in rows]


@router.get("/{patient_id}/records/{record_id}", response_model=MedicalRecordRead)
def get_record(
    patient_id: UUID,
    record_id: UUID,
    db: Session = Depends(get_db),
    patient_id_header: str | None = Header(default=None, alias="patient_id"),
) -> MedicalRecordRead:
    _validate_patient_header(patient_id, patient_id_header)
    row = PatientService(db).get_record(patient_id, record_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return MedicalRecordRead.model_validate(row)


@router.delete("/{patient_id}/records/{record_id}")
def delete_record(
    patient_id: UUID,
    record_id: UUID,
    db: Session = Depends(get_db),
    patient_id_header: str | None = Header(default=None, alias="patient_id"),
) -> dict[str, bool]:
    _validate_patient_header(patient_id, patient_id_header)
    ok = PatientService(db).delete_record(patient_id, record_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"deleted": True}


@router.post("/{patient_id}/prescriptions", response_model=PrescriptionRead)
def add_prescription(
    patient_id: UUID,
    payload: PrescriptionCreate,
    db: Session = Depends(get_db),
    patient_id_header: str | None = Header(default=None, alias="patient_id"),
) -> PrescriptionRead:
    _validate_patient_header(patient_id, patient_id_header)
    row = PatientService(db).add_prescription(patient_id, payload)
    return PrescriptionRead.model_validate(row)


@router.get("/{patient_id}/prescriptions", response_model=list[PrescriptionRead])
def list_prescriptions(
    patient_id: UUID,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    patient_id_header: str | None = Header(default=None, alias="patient_id"),
) -> list[PrescriptionRead]:
    _validate_patient_header(patient_id, patient_id_header)
    rows = PatientService(db).get_prescriptions(patient_id, limit=limit, offset=offset)
    return [PrescriptionRead.model_validate(row) for row in rows]

