from typing import Any

import numpy as np
from _pytest.monkeypatch import MonkeyPatch

from ingestion.ehr_connector import PatientRecord
from preprocessing.deidentification import (
    _add_laplace_noise_to_numeric,
    _generalize_age,
    _generalize_gender,
    _generalize_zipcode,
    _mask_phi_text,
    deidentify_record,
)


def test_mask_phi_text_redacts_email_and_phone() -> None:
    text = "Contact john.doe@example.com or 555-123-4567 on 2025-01-05."
    masked = _mask_phi_text(text)
    assert "[REDACTED_EMAIL]" in masked
    assert "[REDACTED_PHONE]" in masked


def test_generalizers() -> None:
    assert _generalize_age(38) == "35-39"
    assert _generalize_zipcode("12345") == "123**"
    assert _generalize_gender("female") == "F"


def test_add_laplace_noise_to_numeric(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(np.random, "laplace", lambda _loc, _scale: 0.5)
    value = _add_laplace_noise_to_numeric(10.0, epsilon=1.0)
    assert value == 10.5


def test_deidentify_record(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(np.random, "laplace", lambda _loc, _scale: 1.0)
    observation: dict[str, Any] = {
        "age": 42,
        "zipcode": "94107",
        "heart_rate": 72.0,
        "clinical_text": "Patient John Doe email jane@hospital.org.",
    }
    record = PatientRecord(
        patient_id="P123",
        source_system="hl7v2",
        given_name="John",
        family_name="Doe",
        sex="M",
        observation_summary=observation,
    )
    result = deidentify_record(record)
    assert result.patient_id == "P123"
    assert result.quasi_identifiers["age_band"] == "40-44"
    assert result.quasi_identifiers["zipcode_prefix"] == "941**"
    assert result.quasi_identifiers["gender_group"] == "M"
    assert result.structured_record["given_name"] == "[REDACTED]"
    assert result.deidentified_text is not None
    assert "[REDACTED_EMAIL]" in result.deidentified_text
    assert "heart_rate" in result.noisy_numeric_fields

