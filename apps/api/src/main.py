from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import gettempdir
from typing import Any

import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from torch import nn
from typing import cast

from amca_api.config import get_settings
from amca_api.routes import health
from fusion.fusion_router import FusionRouter
from ingestion.ehr_connector import EHRConnector, PatientRecord
from ingestion.imaging_connector import ImagingConnector, ModalityPayload
from monitoring.monitoring_api import router as monitoring_router
from output.feedback_capture import router as feedback_router
from output.fhir_integration import router as fhir_router
from output.integration_api import router as output_router
from preprocessing.preprocessor_pipeline import PreprocessorPipeline, RawIngestionBundle
from reasoning.reasoning_orchestrator import ClinicalRecommendation, ReasoningOrchestrator
from safety.human_in_loop import GatedRecommendation, gate_router
from safety.regulatory_compliance import audit_router
from safety.safety_orchestrator import SafetyBundle, SafetyOrchestrator


class AnalyseResponse(BaseModel):
    gated_recommendation: GatedRecommendation
    safety_bundle: SafetyBundle


class _TinyInferenceModel(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(4, 8), nn.ReLU(), nn.Dropout(0.3), nn.Linear(8, 2))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return cast(torch.Tensor, self.net(x))


settings = get_settings()

app = FastAPI(
    title="Autonomous Multimodal Clinical AI Assistant API",
    version="0.1.0",
    description=(
        "End-to-end multimodal pipeline for ingestion, preprocessing, fusion, reasoning, "
        "safety checks, human gating, monitoring, and healthcare interoperability."
    ),
    contact={"name": "AMCA Platform Team", "email": "amca-support@example.org"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(monitoring_router)
app.include_router(health.router, tags=["health"])
app.include_router(audit_router)
app.include_router(gate_router)
app.include_router(fhir_router)
app.include_router(feedback_router)
app.include_router(output_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "amca-api", "version": "0.1.0"}


def _ensure_tensor_path(dicom_path: str | None) -> str:
    if dicom_path:
        connector = ImagingConnector()
        payload = connector.ingest_file(dicom_path)
        return payload.raw_tensor_path
    path = Path(gettempdir()) / "amca_dummy_tensor.npy"
    if not path.exists():
        np.save(path, np.random.randn(224, 224).astype(np.float32))
    return str(path)


def _build_patient_record(ehr_json: str | None, clinical_note: str | None) -> PatientRecord:
    if ehr_json:
        try:
            data = json.loads(ehr_json)
            if isinstance(data, dict):
                return PatientRecord(**data)
        except Exception:
            pass
    obs = {"clinical_text": clinical_note or "No clinical note provided."}
    return PatientRecord(patient_id="unknown", source_system="hl7v2", observation_summary=obs)


@app.post("/analyse", response_model=AnalyseResponse)
def analyse(
    ehr_json: str | None = Form(default=None),
    dicom_path: str | None = Form(default=None),
    clinical_note: str | None = Form(default=None),
    omics_csv: str | None = Form(default=None),
) -> AnalyseResponse:
    patient_record = _build_patient_record(ehr_json=ehr_json, clinical_note=clinical_note)
    tensor_path = _ensure_tensor_path(dicom_path=dicom_path)
    imaging_payload = ModalityPayload(
        modality_type="ct",
        patient_id=patient_record.patient_id,
        timestamp=datetime.now(timezone.utc),
        raw_tensor_path=tensor_path,
        metadata={"source": "analyse-endpoint"},
    )

    df = pd.DataFrame({"lab_a": [1.0, np.nan, 2.0], "lab_b": [3.0, 2.0, 4.0]})
    raw_bundle = RawIngestionBundle(
        patient_record=patient_record,
        tabular_df=df,
        imaging_payload=imaging_payload,
        coded_entries=[("ICD10", c) for c in patient_record.diagnosis_codes],
    )

    preprocessed = asyncio.run(PreprocessorPipeline().run_pipeline(raw_bundle))
    fused = FusionRouter()(preprocessed)
    recommendation: ClinicalRecommendation = ReasoningOrchestrator().run(fused, patient_record)
    safety_bundle = SafetyOrchestrator().run_safety_checks(
        model=_TinyInferenceModel(),
        input_tensor=torch.randn(1, 4),
        recommendation=recommendation,
    )
    return AnalyseResponse(
        gated_recommendation=safety_bundle.gated_recommendation,
        safety_bundle=safety_bundle,
    )

