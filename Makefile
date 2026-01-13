.PHONY: lint lint-backend lint-frontend test test-backend test-frontend

lint: lint-backend lint-frontend

lint-backend:
	cd backend && poetry install && poetry run ruff check --select F .

lint-frontend:
	cd frontend && npm install && npm run lint

test: test-backend test-frontend

test-backend:
	cd backend && poetry install && poetry run pytest

test-frontend:
	cd frontend && npm install && npm test
