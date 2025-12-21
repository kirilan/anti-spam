.PHONY: help setup install install-dev dev test lint format build up down logs clean migrate db-shell pre-commit

help:
	@echo "Data Deletion Assistant - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup         Complete project setup (env, deps, pre-commit)"
	@echo "  make install       Install backend dependencies (uv)"
	@echo "  make install-dev   Install with dev dependencies"
	@echo "  make dev           Start development environment (Docker)"
	@echo ""
	@echo "Local Development:"
	@echo "  make run-backend   Run backend locally"
	@echo "  make run-worker    Run Celery worker locally"
	@echo "  make run-beat      Run Celery beat locally"
	@echo ""
	@echo "Docker:"
	@echo "  make build         Build Docker images"
	@echo "  make up            Start all services"
	@echo "  make down          Stop all services"
	@echo "  make logs          View container logs"
	@echo "  make clean         Remove containers and volumes"
	@echo ""
	@echo "Database:"
	@echo "  make migrate       Run Alembic migrations"
	@echo "  make migrate-new   Create new migration (m='description')"
	@echo "  make db-shell      Open PostgreSQL shell"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage"
	@echo "  make lint          Run linter"
	@echo "  make format        Format code"
	@echo "  make check         Run all checks (lint + typecheck + test)"
	@echo "  make pre-commit    Run pre-commit hooks on all files"

# ============ Setup ============

setup: .env install-dev pre-commit-install
	@echo ""
	@echo "Setup complete! Run 'make dev' to start the development environment."

.env:
	@if [ ! -f .env ]; then \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
	fi

install:
	cd backend && uv sync

install-dev:
	cd backend && uv sync --all-extras
	cd frontend && npm install

pre-commit-install:
	@if command -v pre-commit > /dev/null; then \
		pre-commit install; \
	else \
		echo "pre-commit not installed. Install with: pip install pre-commit"; \
	fi

dev: up
	@echo ""
	@echo "Development environment started:"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API Docs: http://localhost:8000/docs"

# ============ Local Development ============

run-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

run-worker:
	cd backend && uv run celery -A app.celery_app worker --loglevel=info

run-beat:
	cd backend && uv run celery -A app.celery_app beat --loglevel=info

# ============ Docker ============

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-worker:
	docker compose logs -f celery-worker

clean:
	docker compose down -v --remove-orphans

restart:
	docker compose restart

# ============ Database ============

migrate:
	cd backend && uv run alembic upgrade head

migrate-new:
	cd backend && uv run alembic revision --autogenerate -m "$(m)"

migrate-down:
	cd backend && uv run alembic downgrade -1

migrate-history:
	cd backend && uv run alembic history

db-shell:
	docker compose exec db psql -U postgres -d antispam

db-reset:
	docker compose down -v
	docker compose up -d db redis
	@sleep 3
	docker compose up -d

# ============ Testing ============

test:
	cd backend && uv run pytest

test-v:
	cd backend && uv run pytest -v

test-cov:
	cd backend && uv run pytest --cov=app --cov-report=term-missing

# ============ Code Quality ============

lint:
	cd backend && uv run ruff check app tests

lint-fix:
	cd backend && uv run ruff check --fix app tests

format:
	cd backend && uv run ruff format app tests

typecheck:
	cd backend && uv run mypy app

check: lint typecheck test

pre-commit:
	pre-commit run --all-files
