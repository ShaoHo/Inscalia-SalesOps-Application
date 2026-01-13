# Inscalia SalesOps Application

This repository is a monorepo containing the FastAPI backend, Celery workers, and a React + TypeScript frontend.

## Structure

```
backend/           # FastAPI app, Celery workers, Dockerfile
  app/
  workers/
frontend/          # React + TypeScript app with tests, Dockerfile
.env.example       # Environment variable template
/docker-compose.yml
```

## Prerequisites

- Docker + Docker Compose

## Setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Build and start the stack:

   ```bash
   docker compose up --build
   ```

## Services

| Service | URL | Notes |
| --- | --- | --- |
| API | http://localhost:8000 | Health: `GET /health` |
| Frontend | http://localhost:5173 | Health: `GET /health` |
| Postgres | localhost:5432 | Database for API |
| Redis | localhost:6379 | Broker/results for Celery |

## Local Development

### Backend

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Workers

```bash
cd backend
poetry install
poetry run celery -A workers.celery_app.celery_app worker --loglevel=info
poetry run celery -A workers.celery_app.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
cd frontend
npm test
```

### Linting and Full Test Runs

Run lint checks for both backend and frontend:

```bash
make lint
```

Run all backend + frontend tests locally:

```bash
make test
```

Individual commands:

```bash
cd backend
poetry run ruff check --select F .
poetry run pytest
```

```bash
cd frontend
npm run lint
npm test
```
