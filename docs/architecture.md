# System Architecture

This document describes the architecture of the Autonomous Multimodal Clinical AI Assistant — how data flows through the system, what each layer does, and how the components connect.

---

## High-Level Flow

```
Ingestion → Preprocessing → Fusion → Reasoning → Safety → Output
                                                       ↓
                                          Monitoring ←→ Self-Learning
                                               ↑
                                        (Feedback loop)
```

---

## Layer Breakdown

### 1. Data Ingestion
The entry point of the system. Accepts multimodal clinical data from multiple sources simultaneously.

| Source | Description |
|---|---|
| EHR | Structured patient records (diagnoses, medications, labs) |
| Medical images | DICOM files — X-rays, CT scans, MRIs |
| Clinical notes | Unstructured physician notes and discharge summaries |
| Wearables | Real-time vitals — heart rate, SpO2, temperature |
| Omics | Genomic or proteomic data (future support) |

**Storage:** Raw files → MinIO. Events → Kafka. Structured records → PostgreSQL.

---

### 2. Preprocessing
Cleans and prepares raw inputs before they reach the ML models.

- **De-identification** — removes PHI (names, dates, IDs) before any model sees the data
- **Normalisation** — standardises units, value ranges, and coding systems (ICD-10, SNOMED)
- **Feature extraction** — pulls structured features from unstructured text using NLP

---

### 3. Multimodal Fusion
Combines signals from different modalities into a unified representation.

| Strategy | When used |
|---|---|
| Early fusion | Raw features concatenated before model input |
| Cross-modal attention | Transformer-based alignment across modalities |
| Late fusion | Modality-specific models whose outputs are combined |

**Models involved:**
- Text → `BioClinicalBERT`
- Images → `ResNet-50`
- Fusion head → `Transformer + MLP`

---

### 4. AI Reasoning (LLM + RAG)
The core intelligence layer. Takes the fused embedding and produces clinical outputs.

- **LLM backend** — OpenAI API or local Ollama (`llama3`)
- **RAG pipeline** — retrieves relevant clinical knowledge before generating responses
- **Outputs** — diagnosis support, treatment suggestions, risk scores, natural language explanations

The reasoning layer never makes autonomous decisions. All outputs pass through the Safety layer before reaching a clinician.

---

### 5. Safety Layer
Every prediction passes through here before being surfaced.

| Mechanism | Purpose |
|---|---|
| Human-in-the-loop gate | High-confidence predictions flagged for clinician review |
| Uncertainty estimation | MC Dropout + Conformal Prediction quantify model confidence |
| Bias auditing | Checks for performance disparities across demographic subgroups |
| Audit logging | All decisions logged with cryptographic signatures for traceability |

---

### 6. Output
What the system delivers to end users.

- **Clinical reports** — structured summaries with supporting evidence
- **Risk scores** — readmission risk, survival probability
- **Explainability** — SHAP and LIME visualisations on every prediction
- **AI Nurse Chatbot** — patient-facing assistant with urgency detection and Redis-backed session memory
- **Alerts** — escalation triggers for critical findings

---

### 7. Monitoring & Drift Detection
Continuously checks whether the model's input distribution or performance is degrading.

| Method | What it detects |
|---|---|
| PSI (Population Stability Index) | Feature distribution shift over time |
| KS Test | Changes in univariate distributions |
| MMD (Maximum Mean Discrepancy) | High-dimensional drift in embeddings |
| AUC / F1 tracking | Performance degradation on labelled holdout data |
| Fairness metrics | Drift in model behaviour across subgroups |

When drift is detected, an alert is triggered and the self-learning loop is activated.

---

### 8. Self-Learning Loop
Keeps the system improving from real-world feedback without retraining from scratch.

| Mechanism | How it works |
|---|---|
| RLHF | Clinicians rate outputs; ratings update model preferences |
| Active learning | Model queries clinicians on the examples it's most uncertain about |
| Experience replay | Past labelled cases replayed during fine-tuning to prevent forgetting |
| Federated learning | Planned — allows learning across hospital nodes without sharing raw data |

The feedback loop connects back to the Ingestion layer — new labelled data re-enters the pipeline as training signal.

---

## Data Storage Map

| What | Where | Why |
|---|---|---|
| Patient records | PostgreSQL | Structured, queryable |
| Medical files & images | MinIO | Object storage, S3-compatible |
| Chat sessions | Redis | Fast read/write for real-time chatbot memory |
| Event streams | Kafka + Zookeeper | Durable, high-throughput message queue |

---

## Key Design Decisions

**Why RAG over fine-tuning?**  
RAG lets us ground LLM outputs in retrieved clinical knowledge without expensive fine-tuning on domain data. It also makes the evidence source inspectable — a clinician can see *what* the model retrieved, not just *what* it said.

**Why human-in-the-loop at the Safety layer specifically?**  
Placing the gate after Reasoning but before Output means the AI does all the heavy lifting before a human sees anything, keeping review time short while ensuring no autonomous action is taken.

**Why separate Monitoring from Learning?**  
Monitoring is passive (observe and alert). Learning is active (update the model). Keeping them separate means drift detection can run continuously in production without triggering uncontrolled model updates.

---

## Limitations

- All models are pretrained baselines, not fine-tuned on real hospital data
- Patient data used in development is entirely synthetic
- Not clinically validated or regulatory approved (SaMD)
- Federated learning support is planned but not yet implemented

---

*For setup instructions, see [README.md](../README.md)*
