from types import SimpleNamespace

from _pytest.monkeypatch import MonkeyPatch

from ingestion.ehr_connector import EHRConnector


def test_parse_hl7_message(monkeypatch: MonkeyPatch) -> None:
    connector = EHRConnector()

    fake_segments = [
        ["PID", "", "", "P001", "", "DOE^JANE", "", "19800101", "F"],
        ["PV1", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "ENC-7"],
        ["DG1", "", "", "I10"],
    ]
    monkeypatch.setattr("ingestion.ehr_connector.hl7", SimpleNamespace(parse=lambda _: fake_segments))

    record = connector.parse_hl7_message("dummy")
    assert record.patient_id == "P001"
    assert record.given_name == "JANE"
    assert record.family_name == "DOE"
    assert record.source_system == "hl7v2"
    assert record.diagnosis_codes == ["I10"]


def test_normalize_fhir_resource() -> None:
    connector = EHRConnector()
    resource = {
        "resourceType": "Patient",
        "id": "F123",
        "name": [{"family": "Doe", "given": ["John"]}],
        "birthDate": "1975-05-20",
        "gender": "male",
        "identifier": [{"value": "ENC-FHIR"}],
    }
    record = connector.normalize_fhir_resource(resource)
    assert record.patient_id == "F123"
    assert record.source_system == "fhir_r4"
    assert record.given_name == "John"
    assert record.encounter_id == "ENC-FHIR"


def test_normalize_dicom_dataset() -> None:
    connector = EHRConnector()
    ds = SimpleNamespace(
        PatientID="D001",
        PatientName="DOE^ALICE",
        PatientBirthDate="19900101",
        PatientSex="F",
        AccessionNumber="ACC9",
        Modality="CT",
        StudyInstanceUID="1.2.3",
    )
    record = connector.normalize_dicom_dataset(ds)
    assert record.patient_id == "D001"
    assert record.source_system == "dicom"
    assert record.observation_summary["modality"] == "CT"

