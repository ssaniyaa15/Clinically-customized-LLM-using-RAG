from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

from ingestion.ehr_connector import PatientRecord
from ingestion.imaging_connector import ModalityPayload
from preprocessing.deidentification import DeidentifiedRecord, deidentify_record
from preprocessing.harmonisation import CanonicalCode, HarmonisationService
from preprocessing.image_preprocessing import ImagePreprocessor, ProcessedImagePayload
from preprocessing.imputation_qc import ImputedDataFrame, impute_and_qc


@dataclass
class RawIngestionBundle:
    patient_record: PatientRecord
    tabular_df: pd.DataFrame
    imaging_payload: ModalityPayload
    coded_entries: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class StepRunLog:
    step_name: str
    started_at: datetime
    ended_at: datetime
    duration_ms: float
    success: bool
    outcome: str


@dataclass
class PipelineRunLog:
    run_id: str
    steps: list[StepRunLog] = field(default_factory=list)


@dataclass
class PreprocessedBundle:
    harmonised_codes: list[CanonicalCode]
    deidentified_record: DeidentifiedRecord
    imputed_data: ImputedDataFrame
    processed_image: ProcessedImagePayload
    pipeline_log: PipelineRunLog


class PreprocessorPipeline:
    def __init__(
        self,
        harmoniser: Any = None,
        image_preprocessor: Any = None,
    ) -> None:
        self.harmoniser: HarmonisationService | Any = harmoniser or HarmonisationService()
        self.image_preprocessor: ImagePreprocessor | Any = image_preprocessor or ImagePreprocessor()

    async def run_pipeline(self, raw_input: RawIngestionBundle) -> PreprocessedBundle:
        run_log = PipelineRunLog(run_id=f"run-{int(time.time() * 1000)}")

        harmonised = self._timed_step(
            run_log,
            "harmonisation",
            self._run_harmonisation,
            raw_input.patient_record,
            raw_input.coded_entries,
        )
        deidentified = self._timed_step(
            run_log,
            "deidentification",
            deidentify_record,
            raw_input.patient_record,
        )

        imputed_task = asyncio.to_thread(
            self._timed_step,
            run_log,
            "imputation_qc",
            impute_and_qc,
            raw_input.tabular_df,
        )
        image_task = asyncio.to_thread(
            self._timed_step,
            run_log,
            "image_preprocessing",
            self.image_preprocessor.preprocess,
            raw_input.imaging_payload,
        )
        imputed, processed_image = await asyncio.gather(imputed_task, image_task)

        return PreprocessedBundle(
            harmonised_codes=harmonised,
            deidentified_record=deidentified,
            imputed_data=imputed,
            processed_image=processed_image,
            pipeline_log=run_log,
        )

    def _run_harmonisation(
        self, record: PatientRecord, coded_entries: list[tuple[str, str]]
    ) -> list[CanonicalCode]:
        entries = coded_entries or [("ICD10", code) for code in record.diagnosis_codes]
        mapped: list[CanonicalCode] = []
        for system, code in entries:
            canonical = self.harmoniser.map_code(system=system, code=code)
            if canonical is not None:
                mapped.append(canonical)
        return mapped

    @staticmethod
    def _timed_step(
        run_log: PipelineRunLog,
        step_name: str,
        fn: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        start = datetime.utcnow()
        t0 = time.perf_counter()
        try:
            result = fn(*args, **kwargs)
            success = True
            outcome = "ok"
            return result
        except Exception as exc:  # pragma: no cover - exercised via tests with failure path if needed
            success = False
            outcome = f"error:{type(exc).__name__}"
            raise
        finally:
            end = datetime.utcnow()
            duration_ms = (time.perf_counter() - t0) * 1000.0
            run_log.steps.append(
                StepRunLog(
                    step_name=step_name,
                    started_at=start,
                    ended_at=end,
                    duration_ms=duration_ms,
                    success=success,
                    outcome=outcome,
                )
            )

