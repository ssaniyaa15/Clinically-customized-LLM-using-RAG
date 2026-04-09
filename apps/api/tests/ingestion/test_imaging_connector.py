from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from _pytest.monkeypatch import MonkeyPatch

from ingestion.imaging_connector import ImagingConnector


def test_ingest_dicom(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    connector = ImagingConnector()
    file_path = tmp_path / "scan.dcm"
    file_path.write_text("x", encoding="utf-8")

    fake_ds = SimpleNamespace(PatientID="P9", Modality="MR", StudyInstanceUID="1.2.3")
    monkeypatch.setattr("ingestion.imaging_connector.pydicom", SimpleNamespace(dcmread=lambda _: fake_ds))

    payload = connector.ingest_file(str(file_path), timestamp=datetime(2026, 1, 1))
    assert payload.modality_type == "mri"
    assert payload.patient_id == "P9"
    assert payload.metadata["source_format"] == "dicom"


def test_ingest_nifti(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    connector = ImagingConnector()
    file_path = tmp_path / "brain_mri.nii.gz"
    file_path.write_text("x", encoding="utf-8")

    fake_img = SimpleNamespace(shape=(64, 64, 32))
    monkeypatch.setattr("ingestion.imaging_connector.nib", SimpleNamespace(load=lambda _: fake_img))

    payload = connector.ingest_file(str(file_path), patient_id="A12")
    assert payload.modality_type == "mri"
    assert payload.patient_id == "A12"
    assert payload.metadata["shape"] == (64, 64, 32)

