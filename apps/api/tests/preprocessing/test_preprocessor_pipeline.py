import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from _pytest.monkeypatch import MonkeyPatch

from ingestion.ehr_connector import PatientRecord
from ingestion.imaging_connector import ModalityPayload
from preprocessing.harmonisation import CanonicalCode
from preprocessing.image_preprocessing import ProcessedImagePayload, SegmentationMask
from preprocessing.preprocessor_pipeline import PreprocessorPipeline, RawIngestionBundle


class FakeHarmoniser:
    def map_code(self, system: str, code: str) -> CanonicalCode | None:
        if system == "ICD10" and code == "I10":
            return CanonicalCode(system=system, code=code, canonical_id="C1", canonical_label="HTN")
        return None


class FakeImagePreprocessor:
    def preprocess(self, payload: ModalityPayload) -> ProcessedImagePayload:
        return ProcessedImagePayload(
            normalised_tensor=np.array([1.0, 2.0]),
            augmentation_applied=[],
            mask=SegmentationMask(),
        )


def test_run_harmonisation() -> None:
    pipe = PreprocessorPipeline(harmoniser=FakeHarmoniser(), image_preprocessor=FakeImagePreprocessor())
    record = PatientRecord(patient_id="P1", source_system="hl7v2", diagnosis_codes=["I10"])
    out = pipe._run_harmonisation(record, [])
    assert len(out) == 1
    assert out[0].canonical_id == "C1"


def test_timed_step_logs() -> None:
    from preprocessing.preprocessor_pipeline import PipelineRunLog

    run_log = PipelineRunLog(run_id="x")
    result = PreprocessorPipeline._timed_step(run_log, "step", lambda x: x + 1, 1)
    assert result == 2
    assert run_log.steps[0].step_name == "step"
    assert run_log.steps[0].success is True


def test_run_pipeline_end_to_end(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    pipe = PreprocessorPipeline(harmoniser=FakeHarmoniser(), image_preprocessor=FakeImagePreprocessor())

    async def fake_gather(*tasks: Any) -> list[Any]:
        return [await t for t in tasks]

    monkeypatch.setattr(asyncio, "gather", fake_gather)

    record = PatientRecord(
        patient_id="P9",
        source_system="hl7v2",
        diagnosis_codes=["I10"],
        sex="female",
        observation_summary={"age": 44, "zipcode": "12345", "heart_rate": 70},
    )
    image_payload = ModalityPayload(
        modality_type="ct",
        patient_id="P9",
        timestamp=datetime.utcnow(),
        raw_tensor_path=str(tmp_path / "x.npy"),
        metadata={},
    )
    df = pd.DataFrame({"a": [1.0, None, 2.0], "b": [3.0, 4.0, 5.0]})
    raw_bundle = RawIngestionBundle(patient_record=record, tabular_df=df, imaging_payload=image_payload)

    result = asyncio.run(pipe.run_pipeline(raw_bundle))
    assert len(result.harmonised_codes) == 1
    assert result.deidentified_record.patient_id == "P9"
    assert result.imputed_data.imputation_report["missing_after"] == 0
    assert len(result.pipeline_log.steps) == 4

