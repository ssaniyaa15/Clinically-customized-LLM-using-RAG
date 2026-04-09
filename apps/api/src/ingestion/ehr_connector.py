from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

try:
    import hl7
except ImportError:  # pragma: no cover - covered via mocks/tests
    hl7 = None

try:
    from fhirclient.models.patient import Patient as FhirPatient
except ImportError:  # pragma: no cover - covered via mocks/tests
    FhirPatient = None

try:
    import pydicom
except ImportError:  # pragma: no cover - covered via mocks/tests
    pydicom = None  # type: ignore[assignment]


class PatientRecord(BaseModel):
    patient_id: str
    source_system: str = Field(description="hl7v2|fhir_r4|dicom")
    given_name: str | None = None
    family_name: str | None = None
    date_of_birth: str | None = None
    sex: str | None = None
    encounter_id: str | None = None
    diagnosis_codes: list[str] = Field(default_factory=list)
    observation_summary: dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class EHRConnector:
    """Connector that normalizes HL7, FHIR, and DICOM into PatientRecord."""

    def parse_hl7_message(self, message: str) -> PatientRecord:
        if hl7 is None:
            raise RuntimeError("hl7 dependency not installed.")
        parsed = hl7.parse(message)

        pid_fields: list[str] = []
        pv1_fields: list[str] = []
        diagnoses: list[str] = []

        for segment in parsed:
            seg_type = str(segment[0])
            values = [str(field) for field in segment]
            if seg_type == "PID":
                pid_fields = values
            elif seg_type == "PV1":
                pv1_fields = values
            elif seg_type == "DG1" and len(values) > 3:
                diagnoses.append(values[3])

        patient_id = pid_fields[3] if len(pid_fields) > 3 else "unknown"
        name = pid_fields[5].split("^") if len(pid_fields) > 5 else []
        dob = pid_fields[7] if len(pid_fields) > 7 else None
        sex = pid_fields[8] if len(pid_fields) > 8 else None
        encounter = pv1_fields[19] if len(pv1_fields) > 19 else None

        return PatientRecord(
            patient_id=patient_id,
            source_system="hl7v2",
            given_name=name[1] if len(name) > 1 else None,
            family_name=name[0] if len(name) > 0 else None,
            date_of_birth=dob,
            sex=sex,
            encounter_id=encounter,
            diagnosis_codes=diagnoses,
            observation_summary={"segment_count": len(parsed)},
        )

    def fetch_fhir_patient(self, smart_client: Any, patient_id: str) -> PatientRecord:
        if FhirPatient is None:
            raise RuntimeError("fhirclient dependency not installed.")
        resource = FhirPatient.read(patient_id, smart_client)
        return self.normalize_fhir_resource(resource.as_json())

    def normalize_fhir_resource(self, resource: dict[str, Any]) -> PatientRecord:
        name_entry = (resource.get("name") or [{}])[0]
        given = (name_entry.get("given") or [None])[0]
        family = name_entry.get("family")
        birth_date = resource.get("birthDate")
        gender = resource.get("gender")
        patient_id = resource.get("id", "unknown")
        encounter = (resource.get("identifier") or [{}])[0].get("value")

        return PatientRecord(
            patient_id=patient_id,
            source_system="fhir_r4",
            given_name=given,
            family_name=family,
            date_of_birth=birth_date,
            sex=gender,
            encounter_id=encounter,
            diagnosis_codes=[],
            observation_summary={"resource_type": resource.get("resourceType", "Patient")},
        )

    def parse_dicom_file(self, path: str) -> PatientRecord:
        if pydicom is None:
            raise RuntimeError("pydicom dependency not installed.")
        dataset = pydicom.dcmread(path)
        return self.normalize_dicom_dataset(dataset)

    def normalize_dicom_dataset(self, dataset: Any) -> PatientRecord:
        patient_name = str(getattr(dataset, "PatientName", ""))
        split_name = [n for n in patient_name.split("^") if n]
        return PatientRecord(
            patient_id=str(getattr(dataset, "PatientID", "unknown")),
            source_system="dicom",
            given_name=split_name[1] if len(split_name) > 1 else None,
            family_name=split_name[0] if split_name else None,
            date_of_birth=str(getattr(dataset, "PatientBirthDate", "")) or None,
            sex=str(getattr(dataset, "PatientSex", "")) or None,
            encounter_id=str(getattr(dataset, "AccessionNumber", "")) or None,
            diagnosis_codes=[],
            observation_summary={
                "modality": str(getattr(dataset, "Modality", "")) or None,
                "study_instance_uid": str(getattr(dataset, "StudyInstanceUID", "")) or None,
            },
        )

