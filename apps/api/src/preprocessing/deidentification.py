from __future__ import annotations

import copy
import re
from typing import Any

import numpy as np
from pydantic import BaseModel, Field

from ingestion.ehr_connector import PatientRecord

PHI_PATTERNS: dict[str, str] = {
    "geographic_subdivision": r"\b\d{5}(?:-\d{4})?\b",
    "date": r"\b(?:19|20)\d{2}[-/]?(?:0[1-9]|1[0-2])[-/]?(?:0[1-9]|[12]\d|3[01])\b",
    "phone": r"\b(?:\+?\d{1,2}\s?)?(?:\(?\d{3}\)?[-\s]?)\d{3}[-\s]?\d{4}\b",
    "fax": r"\bfax[:\s]*\+?\d[\d\-\s]{6,}\b",
    "email": r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "medical_record_number": r"\bMRN[:\s-]*[A-Za-z0-9]+\b",
    "health_plan_beneficiary_number": r"\bHPN[:\s-]*[A-Za-z0-9]+\b",
    "account_number": r"\bACC(?:OUNT)?[:\s-]*[A-Za-z0-9]+\b",
    "certificate_license": r"\bLIC(?:ENSE)?[:\s-]*[A-Za-z0-9]+\b",
    "vehicle_identifier": r"\bVIN[:\s-]*[A-Za-z0-9]+\b",
    "device_identifier": r"\bDEVICE[:\s-]*[A-Za-z0-9]+\b",
    "url": r"\bhttps?://\S+\b",
    "ip": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "biometric_identifier": r"\b(?:fingerprint|retina|iris)\b",
    "full_face_photo": r"\bphoto(id)?\b",
    "other_unique_identifier": r"\bUID[:\s-]*[A-Za-z0-9-]+\b",
    "names": r"\b([A-Z][a-z]+)\s([A-Z][a-z]+)\b",
}

PHI_KEYS = {
    "name",
    "first_name",
    "last_name",
    "given_name",
    "family_name",
    "phone",
    "fax",
    "email",
    "ssn",
    "mrn",
    "medical_record_number",
    "account_number",
    "license_number",
    "vin",
    "device_id",
    "url",
    "ip",
    "photo",
    "uid",
    "address",
}


class DeidentifiedRecord(BaseModel):
    patient_id: str
    deidentified_text: str | None = None
    quasi_identifiers: dict[str, str | None] = Field(default_factory=dict)
    structured_record: dict[str, Any] = Field(default_factory=dict)
    noisy_numeric_fields: dict[str, float] = Field(default_factory=dict)
    removed_phi_fields: list[str] = Field(default_factory=list)


def _mask_phi_text(raw_text: str) -> str:
    masked = raw_text
    for label, pattern in PHI_PATTERNS.items():
        masked = re.sub(pattern, f"[REDACTED_{label.upper()}]", masked, flags=re.IGNORECASE)
    return masked


def _generalize_age(age_value: Any) -> str | None:
    if age_value is None:
        return None
    age = int(age_value)
    low = (age // 5) * 5
    return f"{low}-{low + 4}"


def _generalize_zipcode(zipcode: Any) -> str | None:
    if zipcode is None:
        return None
    digits = "".join(ch for ch in str(zipcode) if ch.isdigit())
    if len(digits) < 3:
        return None
    return f"{digits[:3]}**"


def _generalize_gender(gender: Any) -> str | None:
    if gender is None:
        return None
    value = str(gender).strip().lower()
    if value in {"m", "male"}:
        return "M"
    if value in {"f", "female"}:
        return "F"
    return "U"


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float, np.floating, np.integer)) and not isinstance(value, bool)


def _add_laplace_noise_to_numeric(value: Any, epsilon: float = 1.0) -> Any:
    if _is_numeric(value):
        return float(value) + float(np.random.laplace(0.0, 1.0 / epsilon))
    if isinstance(value, dict):
        return {k: _add_laplace_noise_to_numeric(v, epsilon=epsilon) for k, v in value.items()}
    if isinstance(value, list):
        return [_add_laplace_noise_to_numeric(v, epsilon=epsilon) for v in value]
    return value


def deidentify_record(record: PatientRecord) -> DeidentifiedRecord:
    structured = copy.deepcopy(record.model_dump())
    removed_fields: list[str] = []

    for key in list(structured.keys()):
        if key.lower() in PHI_KEYS:
            structured[key] = "[REDACTED]"
            removed_fields.append(key)

    observation = structured.get("observation_summary", {})
    noisy_observation = _add_laplace_noise_to_numeric(observation, epsilon=1.0)
    if isinstance(noisy_observation, dict):
        structured["observation_summary"] = noisy_observation

    quasi = {
        "age_band": _generalize_age(observation.get("age") if isinstance(observation, dict) else None),
        "zipcode_prefix": _generalize_zipcode(
            observation.get("zipcode") if isinstance(observation, dict) else None
        ),
        "gender_group": _generalize_gender(record.sex),
    }

    text_blob = None
    if isinstance(observation, dict):
        text_value = observation.get("clinical_text")
        if isinstance(text_value, str):
            text_blob = _mask_phi_text(text_value)

    noisy_numeric_fields: dict[str, float] = {}
    if isinstance(noisy_observation, dict):
        for key, value in noisy_observation.items():
            if _is_numeric(value):
                noisy_numeric_fields[key] = float(value)

    return DeidentifiedRecord(
        patient_id=record.patient_id,
        deidentified_text=text_blob,
        quasi_identifiers=quasi,
        structured_record=structured,
        noisy_numeric_fields=noisy_numeric_fields,
        removed_phi_fields=removed_fields,
    )

