from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel

from reasoning.reasoning_orchestrator import ClinicalRecommendation


class AuditEntry(BaseModel):
    patient_id: str
    clinician_id: str
    action_taken: str
    timestamp: datetime
    recommendation_payload: dict[str, Any]
    electronic_signature_hash: str


class SaMDMetadata(BaseModel):
    class_: str = "II"
    regulation: str = "FDA 21 CFR Part 11 / EU MDR / ISO 13485"
    version: str


class AuditTrail:
    """Compliance audit trail with electronic signatures for each prediction event."""

    def __init__(self, db_path: str = "apps/api/data/compliance_audit.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id TEXT NOT NULL,
                    clinician_id TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    recommendation_payload TEXT NOT NULL,
                    electronic_signature_hash TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _signature(self, payload: dict[str, Any]) -> str:
        secret = os.getenv("COMPLIANCE_SECRET_KEY", "dev-secret")
        raw = json.dumps(payload, sort_keys=True, default=str) + secret
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def log_prediction(
        self,
        patient_id: str,
        recommendation: ClinicalRecommendation,
        clinician_id: str,
        action_taken: str,
    ) -> AuditEntry:
        payload = recommendation.model_dump()
        signature = self._signature(payload)
        ts = datetime.now(timezone.utc)
        entry = AuditEntry(
            patient_id=patient_id,
            clinician_id=clinician_id,
            action_taken=action_taken,
            timestamp=ts,
            recommendation_payload=payload,
            electronic_signature_hash=signature,
        )
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO audit_entries
                (patient_id, clinician_id, action_taken, timestamp, recommendation_payload, electronic_signature_hash)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.patient_id,
                    entry.clinician_id,
                    entry.action_taken,
                    entry.timestamp.isoformat(),
                    json.dumps(entry.recommendation_payload, default=str),
                    entry.electronic_signature_hash,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return entry

    def list_entries(self, offset: int = 0, limit: int = 50) -> list[AuditEntry]:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT patient_id, clinician_id, action_taken, timestamp, recommendation_payload, electronic_signature_hash
                FROM audit_entries ORDER BY id DESC LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        finally:
            conn.close()
        entries: list[AuditEntry] = []
        for row in rows:
            entries.append(
                AuditEntry(
                    patient_id=row[0],
                    clinician_id=row[1],
                    action_taken=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    recommendation_payload=json.loads(row[4]),
                    electronic_signature_hash=row[5],
                )
            )
        return entries


audit_router = APIRouter(prefix="/compliance", tags=["compliance"])
_audit_trail = AuditTrail()


@audit_router.get("/audit-trail", response_model=list[AuditEntry])
def get_audit_trail(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=500)) -> list[AuditEntry]:
    return _audit_trail.list_entries(offset=offset, limit=limit)


@audit_router.get("/samd-metadata", response_model=SaMDMetadata)
def get_samd_metadata() -> SaMDMetadata:
    version = os.getenv("APP_VERSION", "0.1.0")
    return SaMDMetadata(version=version)

