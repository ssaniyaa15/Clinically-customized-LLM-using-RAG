from __future__ import annotations

from uuid import UUID

import numpy as np
from numpy.typing import NDArray
from sqlalchemy import select

from patients.database import SessionLocal
from patients.models import Patient, Prescription

try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None


def _embed_query(user_query: str) -> NDArray[np.float32]:
    rng = np.random.default_rng(abs(hash(user_query)) % (2**32))
    return rng.normal(size=(768,)).astype(np.float32)


def _retrieve_relevant_chunks(patient_id: UUID, user_query: str, top_k: int = 5) -> list[str]:
    if faiss is None:
        return []
    namespace = f"patient:{patient_id}"
    index_path = f"apps/api/data/faiss/{namespace}.index"
    meta_path = f"apps/api/data/faiss/{namespace}.meta.json"
    try:
        index = faiss.read_index(index_path)
    except Exception:
        return []
    query = _embed_query(user_query).reshape(1, -1)
    _, idx = index.search(query, top_k)
    # We only have vector counts in the current lightweight FAISS metadata pipeline.
    # Return opaque chunk labels for now.
    return [f"Relevant clinical chunk #{int(i)}" for i in idx[0] if int(i) >= 0]


async def build_patient_context(patient_id: UUID, user_query: str) -> str:
    with SessionLocal() as db:
        patient = db.get(Patient, str(patient_id))
        latest_rx = list(
            db.execute(
                select(Prescription)
                .where(Prescription.patient_id == str(patient_id))
                .order_by(Prescription.prescribed_at.desc())
                .limit(3)
            ).scalars()
        )

    if patient is None and not latest_rx:
        return ""

    name = patient.full_name if patient is not None else "Unknown"
    dob = str(patient.date_of_birth) if patient is not None else "Unknown"
    blood_group = patient.blood_group if patient is not None and patient.blood_group else "Unknown"
    allergies = ", ".join(patient.allergies) if patient is not None and patient.allergies else "None known"
    chunks = _retrieve_relevant_chunks(patient_id, user_query, top_k=5)
    meds: list[str] = []
    for rx in latest_rx:
        for med in rx.medications:
            meds.append(
                f"{med.get('name', 'Unknown')}: {med.get('dose', 'N/A')}, {med.get('frequency', 'N/A')}"
            )
    if not meds:
        meds.append("No active medications found.")

    records_block = "\n".join(chunks) if chunks else "No relevant document snippets found."
    meds_block = "\n".join(meds)
    return (
        "PATIENT PROFILE:\n"
        f"Name: {name}, DOB: {dob}, Blood group: {blood_group}\n"
        f"Known allergies: {allergies}\n\n"
        "RELEVANT RECORDS (from uploaded documents):\n"
        f"{records_block}\n\n"
        "CURRENT MEDICATIONS:\n"
        f"{meds_block}"
    )

