# Autonomous Multimodal Clinical AI Assistant (AMCA)

## Architecture Overview

**Ingestion layer (`apps/api/src/ingestion`)** normalizes EHR (HL7/FHIR/DICOM), imaging, wearable, NLP, and omics inputs into canonical payloads. It provides a unified substrate for downstream processing and event publication.

**Preprocessing layer (`apps/api/src/preprocessing`)** performs ontology harmonization, de-identification, tabular imputation/QC, and image normalization/augmentation. It orchestrates sequential + parallel preprocessing stages before model inference.

**Fusion + reasoning layer (`packages/ml-core/src/fusion`, `apps/api/src/reasoning`)** builds multimodal representations (early/cross/late fusion), produces differential diagnosis, treatment, risk prognosis, and explainability outputs, and prepares clinical recommendations.

**Safety + monitoring layer (`apps/api/src/safety`, `apps/api/src/monitoring`)** applies uncertainty checks, subgroup bias auditing, compliance audit trails, human-in-the-loop gating, and drift/performance surveillance with retraining trigger conditions.

**Output + integration layer (`apps/api/src/output`, `apps/web`)** delivers SMART-on-FHIR and HL7/FHIR outputs, clinician feedback capture to RLHF, and a Next.js clinical dashboard with typed backend integration and confirm/override workflows.

## Quick Start

```bash
git clone <your-repo-url>
cd c-PCL-project-2026
cp .env.example .env
make docker-up
```

Open [http://localhost:3000](http://localhost:3000) for the clinical dashboard and [http://localhost:8000/docs](http://localhost:8000/docs) for API docs.

## Environment Variables

| Variable | Purpose | Example |
|---|---|---|
| `API_CORS_ORIGINS` | Allowed frontend origins for FastAPI CORS | `http://localhost:3000` |
| `INTERNAL_API_URL` | Server-side Next.js API base URL | `http://api:8000` |
| `NEXT_PUBLIC_API_URL` | Browser-visible API base URL | `http://localhost:8000` |
| `LLM_BASE_URL` | OpenAI-compatible endpoint for DDx + summaries | `http://localhost:8001/v1` |
| `LLM_MODEL` | LLM model identifier | `gpt-4o-mini` |
| `LLM_API_KEY` | LLM API key/token | `sk-...` |
| `DDX_FAISS_INDEX_PATH` | Local FAISS index path for RAG retrieval | `models/ddx_index.faiss` |
| `DDX_CHUNKS_PATH` | Retrieved corpus chunk file | `models/ddx_chunks.json` |
| `REDIS_URL` | Redis cache URL for retrieval caching | `redis://redis:6379/0` |
| `KAFKA_BOOTSTRAP` | Kafka bootstrap server list | `kafka:9092` |
| `COMPLIANCE_SECRET_KEY` | Signature key for audit log entries | `change-me` |
| `APP_VERSION` | API/application version metadata | `0.1.0` |
| `RETRAIN_PSI_THRESHOLD` | Drift threshold for retraining trigger | `0.2` |
| `RETRAIN_AUC_DROP_THRESHOLD` | AUC degradation threshold | `0.05` |
| `RETRAIN_FAIRNESS_GAP_THRESHOLD` | Fairness gap threshold | `0.1` |
| `UNCERTAINTY_EPI_THRESHOLD` | Epistemic uncertainty escalation threshold | `0.2` |
| `DB_PASSWORD` | Postgres password (docker/k8s) | `postgres` |

## Running Tests

```bash
make test
```

## Triggering Retraining

Use the monitoring ingest endpoint with a drift payload:

```bash
curl -X POST "http://localhost:8000/monitoring/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "reference":[{"a":1.0,"b":2.0},{"a":1.2,"b":2.1}],
    "current":[{"a":2.0,"b":3.0},{"a":2.2,"b":3.1}],
    "predictions":[0.2,0.8],
    "ground_truth":[0,1],
    "sensitive_attrs":[0,1],
    "error_rate":0.25
  }'
```

If thresholds are exceeded, the API returns a retrigger event with `shadow_mode=true`.
