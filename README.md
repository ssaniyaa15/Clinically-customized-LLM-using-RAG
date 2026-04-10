#  Autonomous Multimodal Clinical AI Assistant

> A clinical decision support system integrating multimodal AI, real-time monitoring, and human-in-the-loop validation — built as a full-stack research prototype.


---

## What This Is

A full-stack AI system that simulates how a hospital-grade clinical assistant could work. It ingests multimodal patient data (EHR records, medical images, clinical notes, wearable signals), reasons over them using an LLM + RAG pipeline, and surfaces decisions with explainability, uncertainty estimates, and drift alerts — always keeping a clinician in the loop.

The goal isn't to replace doctors. It's to show what responsible AI infrastructure in healthcare could look like.

---

## Architecture
→ [Full architecture breakdown](/docs/architecture.md)
Ingestion → Preprocessing → Fusion → Reasoning → Safety → Output
↓
Monitoring & Self-Learning

| Layer | What it does |
|---|---|
| **Ingestion** | Collects EHR, imaging, notes, wearable streams |
| **Preprocessing** | De-identification, normalization, standardization |
| **Fusion** | Early fusion, cross-modal attention, late fusion |
| **Reasoning** | LLM + RAG for diagnosis support and treatment suggestions |
| **Safety** | Uncertainty estimation, bias auditing, human validation gate |
| **Output** | Clinical reports, risk scores, chatbot responses, alerts |
| **Monitoring** | Drift detection (PSI, KS, MMD), AUC/F1 tracking |
| **Learning** | RLHF from clinician feedback, active learning, experience replay |

---

## Key Features

**Multimodal Reasoning**
Combines structured EHR data, unstructured clinical notes (BioClinicalBERT), and medical images (ResNet-50) through transformer-based fusion.

**LLM + RAG Pipeline**
Context-aware diagnosis support and explanations grounded in retrieved clinical knowledge. Supports OpenAI or local Ollama (llama3).

**24/7 AI Nurse Chatbot**
Patient-facing assistant with urgency detection (normal → emergency escalation), Redis-backed session memory, and safe response guardrails.

**Risk & Prognosis Prediction**
Readmission risk scoring and survival analysis using logistic regression on fused embeddings.

**Explainability**
SHAP and LIME explanations on every prediction — because black-box AI has no place in clinical settings.

**Drift Detection**
PSI (Population Stability Index), KS tests, and MMD monitor for distribution shift in incoming data over time.

**Self-Learning Loop**
RLHF from clinician feedback, uncertainty-based active learning, and continual learning with experience replay.

---

## ML Components

| Component | Approach |
|---|---|
| Clinical text | BioClinicalBERT |
| Medical imaging | ResNet-50 |
| Multimodal fusion | Transformer + MLP |
| Risk prediction | Logistic Regression |
| Reasoning | LLM (OpenAI / Ollama) + RAG |
| Explainability | SHAP, LIME |
| Drift detection | PSI, KS Test, MMD |

---

## Tech Stack

**Backend:** FastAPI (Python 3.11), PyTorch, scikit-learn, HuggingFace Transformers  
**Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui  
**Infrastructure:** Docker Compose, PostgreSQL, Redis, Kafka + Zookeeper, MinIO  

---

## Getting Started

### Prerequisites

- Docker Desktop
- Ollama (for local LLM inference)
- Node.js / Python 3.11 (optional, for local dev outside Docker)

### 1. Clone & configure

```bash
git clone https://github.com/your-username/PCL_project_2026
cd PCL_project_2026
cp .env.example .env
```

### 2. Set up local LLM (Ollama)

In your `.env`:

```env
LLM_BASE_URL=http://host.docker.internal:11434
LLM_MODEL=llama3
LLM_API_KEY=dummy
```

Pull and start the model:

```bash
ollama run llama3
```

### 3. Launch

```bash
docker-compose up --build
```

### 4. Access

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API docs | http://localhost:8000/docs |

---

## Data Storage

| Data type | Store |
|---|---|
| Patient records | PostgreSQL |
| Medical files & images | MinIO |
| Chat sessions | Redis |
| Event streams | Kafka |

---

## Safety & Compliance Design

- **Human-in-the-loop gate** on all high-stakes predictions
- **Uncertainty estimation** via MC Dropout and Conformal Prediction
- **Bias auditing** across demographic subgroups
- **Cryptographically signed audit logs**
- Architecture follows SaMD (Software as a Medical Device) design principles

---

## Limitations

This is a research prototype with simulated data. Specifically:

- All patient data is synthetic / demo only
- Models are pretrained baselines — not fine-tuned on real clinical data
- Not evaluated on real hospital datasets
- Not clinically validated or regulatory approved

---

## Roadmap

- [ ] FHIR API integration for real EHR connectivity
- [ ] Fine-tuned clinical LLM (e.g., on MIMIC-IV)
- [ ] Advanced survival models (Cox PH, DeepSurv)
- [ ] Federated learning across hospital nodes
- [ ] Cloud deployment (AWS/GCP)

---

## Built By

**Saniya Bhilare**  
Computer Science Engineering, Jain University, Bangalore  
[LinkedIn](https://www.linkedin.com/in/saniya-bhilare/) · [GitHub](https://github.com/ssaniyaa15)

---

## Acknowledgements

HuggingFace · OpenAI · Ollama · PyTorch · scikit-learn
