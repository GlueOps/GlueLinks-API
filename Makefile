.PHONY: help install run stop clean test logs dev dev-down dev-clean dev-logs dev-test

help:
	@echo "GlueLinks API - Development Commands"
	@echo ""
	@echo "  make install    Install dependencies with pipenv"
	@echo "  make run        Start the API locally (with Valkey)"
	@echo "  make stop       Stop all containers"
	@echo "  make clean      Clean up containers and volumes"
	@echo "  make test       Test the API with curl"
	@echo "  make logs       Show Valkey logs"
	@echo ""
	@echo "  make dev        Start full dev stack (API + Valkey) with mock data"
	@echo "  make dev-down   Stop the dev stack"
	@echo "  make dev-clean  Stop dev stack and remove volumes"
	@echo "  make dev-logs   Tail dev stack logs"
	@echo "  make dev-test   Test all dev/mock endpoints"

install:
	pipenv install

run:
	@chmod +x run-local.sh
	@./run-local.sh

stop:
	docker compose down

clean:
	docker compose down -v
	rm -rf __pycache__ .pytest_cache

test:
	@echo "Testing health endpoint..."
	@curl -s http://localhost:8000/api/v1/health | jq
	@echo ""
	@echo "Testing links endpoint..."
	@curl -s http://localhost:8000/api/v1/applications/taco-backend-prod/links \
		-H "Argocd-Application-Name: nonprod:taco-backend-prod" | jq

logs:
	docker compose logs -f valkey

# ── Dev stack (Docker Compose, mock mode, no K8s needed) ──────────────

dev:
	docker compose -f docker-compose.dev.yml up --build

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-clean:
	docker compose -f docker-compose.dev.yml down -v

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev-test:
	@echo "==> Health"
	@curl -s http://localhost:8000/api/v1/health | jq
	@echo ""
	@echo "==> Fixture: all-ok"
	@curl -s http://localhost:8000/api/v1/fixtures/all-ok | jq
	@echo ""
	@echo "==> Fixture: error-states"
	@curl -s http://localhost:8000/api/v1/fixtures/error-states | jq
	@echo ""
	@echo "==> Fixture: partial-data"
	@curl -s http://localhost:8000/api/v1/fixtures/partial-data | jq
	@echo ""
	@echo "==> Fixture: minimal"
	@curl -s http://localhost:8000/api/v1/fixtures/minimal | jq
	@echo ""
	@echo "==> Mock: test-app"
	@curl -s http://localhost:8000/api/v1/mock/applications/test-app/links | jq
	@echo ""
	@echo "==> Links (mock mode): taco-backend-prod"
	@curl -s http://localhost:8000/api/v1/applications/taco-backend-prod/links \
		-H "Argocd-Application-Name: nonprod:taco-backend-prod" | jq
