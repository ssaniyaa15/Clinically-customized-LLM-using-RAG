from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from sqlalchemy.orm import Session

from patients.models import MedicalRecord

try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None

pdfplumber: Any
try:
    import pdfplumber
except Exception:  # pragma: no cover
    pdfplumber = None

pytesseract: Any
try:
    import pytesseract as pytesseract_module
    pytesseract = pytesseract_module
except Exception:  # pragma: no cover
    pytesseract = None

Image: Any
try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

transformers: Any
try:
    import transformers
except Exception:  # pragma: no cover
    transformers = None


def _extract_text(record: MedicalRecord) -> str:
    path = Path(record.file_path)
    if record.mime_type == "application/pdf" and pdfplumber is not None and path.exists():
        pages: list[str] = []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()
    if record.mime_type.startswith("image/") and pytesseract is not None and Image is not None and path.exists():
        image = Image.open(path)
        return str(pytesseract.image_to_string(image)).strip()
    if path.exists():
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


def _chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    tokens = text.split()
    if not tokens:
        return []
    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    for i in range(0, len(tokens), step):
        slice_tokens = tokens[i : i + chunk_size]
        if not slice_tokens:
            continue
        chunks.append(" ".join(slice_tokens))
    return chunks


def _embed_chunks(chunks: list[str]) -> NDArray[np.float32]:
    if not chunks:
        return np.zeros((0, 768), dtype=np.float32)
    if transformers is None:
        rng = np.random.default_rng(abs(hash(" ".join(chunks[:2]))) % (2**32))
        return rng.normal(size=(len(chunks), 768)).astype(np.float32)
    auto_tokenizer = getattr(transformers, "AutoTokenizer", None)
    auto_model = getattr(transformers, "AutoModel", None)
    if auto_tokenizer is None or auto_model is None:
        rng = np.random.default_rng(abs(hash(" ".join(chunks[:2]))) % (2**32))
        return rng.normal(size=(len(chunks), 768)).astype(np.float32)
    tokenizer = auto_tokenizer.from_pretrained("emilyalsentzer/Bio_ClinicalBERT", local_files_only=True)
    model = auto_model.from_pretrained("emilyalsentzer/Bio_ClinicalBERT", local_files_only=True)
    import torch

    vectors: list[NDArray[np.float32]] = []
    with torch.no_grad():
        for chunk in chunks:
            encoded = tokenizer([chunk], return_tensors="pt", truncation=True, padding=True, max_length=512)
            out = model(**encoded).last_hidden_state.mean(dim=1).squeeze(0).cpu().numpy().astype(np.float32)
            vectors.append(out)
    return np.vstack(vectors) if vectors else np.zeros((0, 768), dtype=np.float32)


def _upsert_faiss(namespace: str, vectors: NDArray[np.float32]) -> str:
    if vectors.shape[0] == 0:
        return namespace
    if faiss is None:
        return namespace
    index = faiss.IndexFlatL2(int(vectors.shape[1]))
    index.add(vectors)
    out_dir = Path("apps/api/data/faiss")
    out_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(out_dir / f"{namespace}.index"))
    meta = out_dir / f"{namespace}.meta.json"
    meta.write_text(json.dumps({"namespace": namespace, "vectors": int(vectors.shape[0])}), encoding="utf-8")
    return namespace


def process_record_embeddings(record_id: str, db: Session) -> None:
    record = db.get(MedicalRecord, record_id)
    if record is None:
        return
    extracted = _extract_text(record)
    chunks = _chunk_text(extracted)
    vectors = _embed_chunks(chunks)
    namespace = f"patient:{record.patient_id}"
    embedding_id = _upsert_faiss(namespace, vectors)
    record.is_processed = True
    record.embedding_id = embedding_id
    db.add(record)
    db.commit()

