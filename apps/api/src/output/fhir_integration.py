from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from reasoning.reasoning_orchestrator import ClinicalRecommendation
from shared.llm_client import llm_complete

router = APIRouter(prefix="/fhir", tags=["fhir"])


class DiagnosticReportPayload(BaseModel):
    patient_id: str
    recommendation: ClinicalRecommendation


async def generate_diagnostic_narrative(rec: ClinicalRecommendation) -> str:
    top_diagnosis = rec.ddx.diagnoses[0].name if rec.ddx.diagnoses else "Unknown"
    top_treatment = (
        rec.treatment.recommendations[0].intervention
        if rec.treatment.recommendations
        else "None"
    )
    readmission = getattr(rec.risk, "readmission_risk", rec.risk.readmission)
    response = await llm_complete(
        system_prompt=(
            "You are a clinical documentation assistant. Write a formal diagnostic narrative "
            "for a FHIR DiagnosticReport."
        ),
        user_prompt=(
            f"Top diagnosis: {top_diagnosis}\n"
            f"Treatment: {top_treatment}\n"
            f"Risk: {readmission.risk_tier}"
        ),
        temperature=0.1,
        max_tokens=500,
    )
    return response.content


def generate_smart_manifest() -> dict[str, object]:
    return {
        "client_id": "amca-smart-app",
        "scope": "launch/patient patient/DiagnosticReport.write patient/Observation.read",
        "redirect_uris": ["https://amca.local/smart/callback"],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",
        "application_type": "web",
    }


def build_diagnostic_report(rec: ClinicalRecommendation, patient_id: str) -> dict[str, object]:
    top = rec.ddx.diagnoses[0] if rec.ddx.diagnoses else None
    try:
        narrative = asyncio.run(generate_diagnostic_narrative(rec))
    except Exception:
        narrative = "AI-generated diagnostic narrative unavailable."
    return {
        "resourceType": "DiagnosticReport",
        "status": "final",
        "code": {"text": "AI Clinical Recommendation"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "effectiveDateTime": rec.generated_at.isoformat(),
        "conclusion": (
            f"Top diagnosis: {top.name} ({top.icd10_code}) confidence={top.confidence:.2f}" if top else "No DDx"
        ),
        "presentedForm": [
            {
                "contentType": "text/plain",
                "data": f"Risk tier: {rec.risk.readmission.risk_tier}; uncertainty={rec.uncertainty_score:.2f}",
            }
        ],
        "text": {"status": "generated", "div": f"<div xmlns=\"http://www.w3.org/1999/xhtml\">{narrative}</div>"},
    }


def build_oru_message(rec: ClinicalRecommendation) -> str:
    top = rec.ddx.diagnoses[0] if rec.ddx.diagnoses else None
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    msh = f"MSH|^~\\&|AMCA|HOSP|EHR|HOSP|{timestamp}||ORU^R01|1|P|2.5"
    pid = "PID|||UNKNOWN||DOE^JOHN"
    obr = "OBR|1|||AMCA^AI Recommendation"
    obx1 = (
        f"OBX|1|TX|DDX||{top.name}^{top.icd10_code}^{top.confidence:.2f}" if top else "OBX|1|TX|DDX||NONE"
    )
    obx2 = f"OBX|2|TX|RISK||{rec.risk.readmission.risk_tier}"
    return "\r".join([msh, pid, obr, obx1, obx2]) + "\r"


@router.get("/smart-manifest")
def get_smart_manifest() -> dict[str, object]:
    return generate_smart_manifest()


@router.post("/diagnostic-report")
def post_diagnostic_report(payload: DiagnosticReportPayload) -> dict[str, object]:
    return build_diagnostic_report(payload.recommendation, payload.patient_id)

