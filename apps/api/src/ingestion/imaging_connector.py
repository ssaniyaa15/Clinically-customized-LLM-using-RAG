from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import pydicom
except ImportError:  # pragma: no cover
    pydicom = None  # type: ignore[assignment]

try:
    import nibabel as nib
except ImportError:  # pragma: no cover
    nib = None  # type: ignore[assignment]


@dataclass
class ModalityPayload:
    modality_type: str
    patient_id: str
    timestamp: datetime
    raw_tensor_path: str
    metadata: dict[str, Any]


class ImagingConnector:
    def ingest_file(
        self,
        file_path: str,
        patient_id: str | None = None,
        timestamp: datetime | None = None,
    ) -> ModalityPayload:
        path = Path(file_path)
        lower = path.name.lower()
        ts = timestamp or datetime.utcnow()

        if lower.endswith(".dcm"):
            return self._ingest_dicom(path, patient_id, ts)
        if lower.endswith(".nii") or lower.endswith(".nii.gz"):
            return self._ingest_nifti(path, patient_id, ts)
        raise ValueError("Unsupported imaging format. Expected DICOM (.dcm) or NIfTI (.nii/.nii.gz).")

    def _ingest_dicom(
        self, path: Path, patient_id: str | None, timestamp: datetime
    ) -> ModalityPayload:
        if pydicom is None:
            raise RuntimeError("pydicom dependency not installed.")
        ds = pydicom.dcmread(str(path))
        modality_code = str(getattr(ds, "Modality", "UNKNOWN")).upper()
        modality_map = {
            "CT": "ct",
            "MR": "mri",
            "CR": "xray",
            "DX": "xray",
            "US": "ultrasound",
            "SM": "pathology_slide",
        }
        modality_type = modality_map.get(modality_code, "unknown")
        pid = patient_id or str(getattr(ds, "PatientID", "unknown"))
        metadata = {
            "source_format": "dicom",
            "dicom_modality": modality_code,
            "study_instance_uid": str(getattr(ds, "StudyInstanceUID", "")),
        }
        return ModalityPayload(modality_type, pid, timestamp, str(path), metadata)

    def _ingest_nifti(
        self, path: Path, patient_id: str | None, timestamp: datetime
    ) -> ModalityPayload:
        if nib is None:
            raise RuntimeError("nibabel dependency not installed.")
        image = nib.load(str(path))
        filename = path.name.lower()
        modality_type = self._infer_modality_from_name(filename)
        metadata = {
            "source_format": "nifti",
            "shape": tuple(int(s) for s in getattr(image, "shape")),  # nibabel runtime object
        }
        pid = patient_id or "unknown"
        return ModalityPayload(modality_type, pid, timestamp, str(path), metadata)

    @staticmethod
    def _infer_modality_from_name(filename: str) -> str:
        if "ct" in filename:
            return "ct"
        if "mri" in filename or "mr" in filename:
            return "mri"
        if "xray" in filename or "xr" in filename:
            return "xray"
        if "ultrasound" in filename or "us" in filename:
            return "ultrasound"
        if "path" in filename or "slide" in filename:
            return "pathology_slide"
        return "unknown"

