from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, Field
from shared.llm_client import llm_complete

transformers: Any
try:
    import transformers
except Exception:  # pragma: no cover
    transformers = None

try:
    import faiss
except Exception:  # pragma: no cover
    faiss = None

redis_module: Any
try:
    import redis as redis_module
except Exception:  # pragma: no cover
    redis_module = None


class Diagnosis(BaseModel):
    name: str
    icd10_code: str
    confidence: float
    evidence_snippets: list[str] = Field(default_factory=list)


class DDxOutput(BaseModel):
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    parse_error: bool = False


@dataclass
class RetrievedChunk:
    text: str
    score: float


class DifferentialDiagnosisHead:
    """RAG-based differential diagnosis using FAISS retrieval and a local LLM."""

    def __init__(self) -> None:
        self.index_path = os.getenv("DDX_FAISS_INDEX_PATH", "models/ddx_index.faiss")
        self.chunks_path = os.getenv("DDX_CHUNKS_PATH", "models/ddx_chunks.json")
        self.redis_client = self._build_redis_client()
        self.encoder = self._build_encoder()
        self.index = self._load_index()
        self.chunks = self._load_chunks()

    @staticmethod
    def _build_redis_client() -> Any:
        if redis_module is None:
            return None
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            return redis_module.from_url(url, decode_responses=True)
        except Exception:
            return None

    def _build_encoder(self) -> Any:
        if transformers is None:
            return None
        auto_model = getattr(transformers, "AutoModel", None)
        auto_tokenizer = getattr(transformers, "AutoTokenizer", None)
        if auto_model is None or auto_tokenizer is None:
            return None
        try:
            tokenizer = auto_tokenizer.from_pretrained(
                "emilyalsentzer/Bio_ClinicalBERT", local_files_only=True
            )
            model = auto_model.from_pretrained("emilyalsentzer/Bio_ClinicalBERT", local_files_only=True)
            return (tokenizer, model)
        except Exception:
            return None

    def _load_index(self) -> Any:
        if faiss is None:
            return None
        if not os.path.exists(self.index_path):
            return None
        return faiss.read_index(self.index_path)

    def _load_chunks(self) -> list[str]:
        if not os.path.exists(self.chunks_path):
            return []
        with open(self.chunks_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return [str(x) for x in data]

    def _embed_query(self, query: str) -> NDArray[np.float32]:
        if self.encoder is None:
            seed = abs(hash(query)) % (2**32)
            rng = np.random.default_rng(seed)
            return rng.normal(size=(768,)).astype(np.float32)

        tokenizer, model = self.encoder
        import torch

        with torch.no_grad():
            encoded = tokenizer([query], return_tensors="pt", truncation=True, padding=True)
            out = model(**encoded).last_hidden_state.mean(dim=1).squeeze(0).cpu().numpy()
        return cast(NDArray[np.float32], out.astype(np.float32))

    def _retrieve(self, query_embedding: NDArray[np.float32], top_k: int = 5) -> list[RetrievedChunk]:
        cache_key = f"ddx:retrieval:{hash(query_embedding.tobytes())}:{top_k}"
        if self.redis_client is not None:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    cached_rows = json.loads(cached)
                    return [RetrievedChunk(text=str(r["text"]), score=float(r["score"])) for r in cached_rows]
            except Exception:
                pass
        if self.index is None or not self.chunks:
            return []
        distances, indices = self.index.search(query_embedding.reshape(1, -1), top_k)
        rows: list[RetrievedChunk] = []
        for score, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            rows.append(RetrievedChunk(text=self.chunks[idx], score=float(score)))
        if self.redis_client is not None:
            try:
                self.redis_client.setex(
                    cache_key,
                    int(os.getenv("DDX_CACHE_TTL_SECONDS", "300")),
                    json.dumps([{"text": r.text, "score": r.score} for r in rows]),
                )
            except Exception:
                pass
        return list(rows)

    @staticmethod
    def _build_user_prompt(patient_context: str, retrieved: list[RetrievedChunk]) -> str:
        retrieved_chunks = "\n".join([chunk.text for chunk in retrieved]) or "No evidence retrieved."
        return (
            f"Patient context:\n{patient_context}\n\n"
            f"Retrieved evidence:\n{retrieved_chunks}\n\n"
            "Return JSON: [{'name': str, 'icd10_code': str, 'confidence': float, "
            "'evidence_snippets': [str]}]"
        )

    async def _call_llm(self, patient_context: str, retrieved: list[RetrievedChunk]) -> str:
        response = await llm_complete(
            system_prompt=(
                "You are a clinical AI assistant. You MUST:\n"
                "* Only answer healthcare-related questions.\n"
                "* Use ONLY the provided patient medical context.\n"
                "* If the question is not medical, respond exactly: "
                "'I can only assist with health-related queries.'\n"
                "* Never hallucinate facts not present in patient data.\n"
                "* Never provide a definitive diagnosis.\n"
                "* Always recommend consulting a doctor.\n"
                "Return only a JSON array of differential diagnoses."
            ),
            user_prompt=self._build_user_prompt(patient_context=patient_context, retrieved=retrieved),
            json_mode=True,
        )
        return response.content

    @staticmethod
    def _parse_response(raw: str) -> DDxOutput:
        try:
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("Expected JSON list of diagnoses")
            diagnoses = [Diagnosis(**item) for item in data]
        except Exception:
            return DDxOutput(diagnoses=[], parse_error=True)
        output = DDxOutput(diagnoses=diagnoses, parse_error=False)
        ranked = sorted(output.diagnoses, key=lambda d: d.confidence, reverse=True)
        return DDxOutput(diagnoses=ranked, parse_error=False)

    def run(self, query: str) -> DDxOutput:
        emb = self._embed_query(query)
        retrieved = self._retrieve(emb, top_k=5)
        response = asyncio.run(self._call_llm(patient_context=query, retrieved=retrieved))
        return self._parse_response(response)

