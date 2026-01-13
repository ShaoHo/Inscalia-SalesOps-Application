# SalesOps Autopilot — Acceptance Checklist (PRD v1.1)

This checklist maps PRD requirements to the current implementation surfaces (API endpoints, database tables, tests, and UI). It also includes reproducible commands for running the stack and a demo flow.

## Acceptance checklist

| Requirement | Endpoint(s) | DB tables | Tests | UI surface |
| --- | --- | --- | --- | --- |
| **FR-1: Natural language input → JSON intent schema validation** | `POST /intents` | _N/A_ (validation only) | `backend/tests/test_intents.py` | NL prompt box + recent intents log in the main app view. |
| **FR-2: Company search & market discovery (LinkedIn/Crunchbase/region sources)** | _Worker tasks only (no API surface yet)._ | `accounts`, `pipeline` (future persistence) | `backend/tests/test_workers.py::test_company_search_task` | Company list in the UI (static seed data). |
| **FR-3: Contact identification + email retrieval (LinkedIn → MailScout → theHarvester)** | _Worker tasks only (no API surface yet)._ | `contacts`, `emails` | `backend/tests/test_workers.py::test_contact_finder_task` | Contact panel with email + phone fields. |
| **FR-4: News collection + background research (NewsAPI + Google News fallback + newspaper3k)** | _Worker tasks only (no API surface yet)._ | `artifacts` (future) | `backend/tests/test_workers.py::test_news_collector_task` | No dedicated UI panel yet. |
| **FR-5: 5-step outbound sequence (multi-language)** | _Worker tasks only (no API surface yet)._ | `email_steps` | `backend/tests/test_workers.py::test_email_generator_task`, `::test_scheduler_task` | Email Sequence (5-step) panel. |
| **FR-6: Pipeline Kanban stages** | _No API yet._ | `pipeline` | `backend/tests/test_models.py::test_crud_models` | Pipeline Kanban board with required stages. |
| **FR-7: BANT qualification** | _Worker tasks only (no API surface yet)._ | `bant` | `backend/tests/test_workers.py::test_pipeline_bant_task` | BANT Qualification panel. |
| **Failure handling + dead-letter visibility** | `GET /deadletter` | `audit_log` (audit trail) | `backend/tests/test_orchestrator.py::test_failure_can_deadletter`, `::test_deadletter_store_records_retry_exhaustion` | No dedicated UI yet (API exposes list). |
| **Health + metrics (operational readiness)** | `GET /health`, `GET /metrics` | _N/A_ | `backend/tests/test_health_metrics.py` | No UI (service checks). |

> **Note:** Several PRD requirements are implemented in worker/orchestrator layers and tests but are not wired to public API endpoints or persisted DB flows yet. The checklist above reflects the current implementation surfaces.

---

## Repro commands

### DB + Redis (docker only)
```bash
docker compose up postgres redis
```

### Backend API (local dev)
```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery workers (local dev)
```bash
cd backend
poetry install
poetry run celery -A workers.celery_app.celery_app worker --loglevel=info
```

### Celery beat (local dev)
```bash
cd backend
poetry install
poetry run celery -A workers.celery_app.celery_app beat --loglevel=info
```

### Frontend (local dev)
```bash
cd frontend
npm install
npm run dev
```

### Full stack (docker)
```bash
docker compose up --build
```

---

## Demo flow (happy path)

1. **Start dependencies:**
   ```bash
   docker compose up postgres redis
   ```
2. **Start API + workers + beat (local dev terminals):**
   ```bash
   cd backend
   poetry install
   poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   ```bash
   cd backend
   poetry run celery -A workers.celery_app.celery_app worker --loglevel=info
   ```
   ```bash
   cd backend
   poetry run celery -A workers.celery_app.celery_app beat --loglevel=info
   ```
3. **Start frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. **Post a sample intent (schema validation):**
   ```bash
   curl -X POST http://localhost:8000/intents \
     -H "Content-Type: application/json" \
     -d '{
       "intent_id": "intent-demo-1",
       "raw_text": "Find APAC SaaS companies with RevOps leaders.",
       "language": "en",
       "filters": {
         "industries": ["SaaS"],
         "regions": ["APAC"],
         "company_size": "20-200",
         "keywords": ["RevOps"],
         "roles": ["Head of RevOps"]
       },
       "actions": ["search_companies", "find_contacts", "generate_emails"]
     }'
   ```
5. **Open UI:** visit `http://localhost:5173` and review the company list, contact panel, email sequence, pipeline kanban, and BANT panels.
6. **Inspect dead letters (if any):**
   ```bash
   curl http://localhost:8000/deadletter
   ```
