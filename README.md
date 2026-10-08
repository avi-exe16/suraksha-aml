# Suraksha AML

Real-time transaction monitoring, behavioral anomaly detection, and automated regulatory compliance platform.

- **Live Demo:** [https://suraksha-aml.vercel.app](https://suraksha-aml.vercel.app)
- **API Docs:** [https://suraksha-aml.onrender.com/docs](https://suraksha-aml.onrender.com/docs)
- **Author:** Abhishek Shandilya (VIT Bhopal University)

---

## Overview

Suraksha monitors banking transactions in real time. It pairs an unsupervised Isolation Forest with statutory compliance overrides to detect fraud patterns, provide local feature attributions via SHAP, and auto-generate regulatory filings within a sub-5ms critical inference path.

---

## Architecture & Data Flow

1. **Ingestion Layer:** FastAPI receives inbound transaction payloads with strict schema validation.
2. **Deterministic Compliance Filter:** Statutory sanctions watchlists (e.g., `USR_SANCTION_FLAGGED`) and FIU-IND limits immediately enforce high-risk blocks.
3. **Behavioral ML Engine:** Isolation Forest analyzes 15 streaming behavioral vectors (velocity spikes, geospatial displacement, amount deviations).
4. **Local Explainability:** SHAP values calculate per-feature risk attributions for auditable decision logging.
5. **Decoupled Event Streaming:** Risk evaluations return immediately to the client; transaction persistence is dispatched asynchronously via **Redis Streams**.
6. **Persistence & Compliance:** Background consumer daemons ingest records into PostgreSQL, enabling instant FIU-IND Suspicious Transaction Report (STR) PDF generation.

---

## Key Features

- **Sub-5ms Inference SLA:** Direct memory scoring path with decoupled asynchronous database writes.
- **Explainable Decisions:** SHAP TreeExplainer surfaces exact anomaly drivers for compliance audits.
- **Automated Filing:** One-click generation of FIU-IND compliant Suspicious Transaction Reports (PDF).
- **DPDP Act 2023 Readiness:** Built-in customer consent lifecycle management and data access audit logging.
- **Operational Controls:** Non-blocking shadow mode toggle for live production canary evaluation.

---

## Model Benchmark

- **Synthetic Baseline:** 78,299 samples | **0.9826 ROC-AUC** | 1.4% False Positive Rate
- **Out-of-Sample Kaggle Validation:** 284,807 unseen records | **0.9016 ROC-AUC**

---

## Tech Stack

- **Backend:** FastAPI, Python 3.11, Uvicorn, Pydantic
- **Message Broker:** Redis Streams
- **Data & Storage:** PostgreSQL, asyncpg, SQLAlchemy
- **Machine Learning & XAI:** Scikit-learn (Isolation Forest), SHAP, NumPy
- **Reporting:** ReportLab (PDF)
- **Frontend:** React, Tailwind CSS, Recharts, Lucide React
- **Hosting:** Render (API & Workers), Vercel (Web Dashboard)

---

## Core API Endpoints

- `POST /transaction/score` — Score incoming transaction against ML and sanctions engine
- `GET /transactions` — Paginated list of scored transactions
- `GET /transactions/{id}` — Individual transaction inspection with SHAP factor contributions
- `GET /transactions/{id}/report` — Download official FIU-IND STR report in PDF format
- `GET /dashboard/stats` — High-level telemetry, risk tier breakdowns, and velocity metrics
- `POST /shadow-mode/toggle` — Toggle non-blocking shadow evaluation mode
- `GET /health` — Health check endpoint for cluster monitoring

---

## Local Development

### 1. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
