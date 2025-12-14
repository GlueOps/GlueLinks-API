.PHONY: help install run stop clean test

help:
	@echo "GlueLinks API - Development Commands"
	@echo ""
	@echo "  make install    Install dependencies with pipenv"
	@echo "  make run        Start the API locally (with Valkey)"
	@echo "  make stop       Stop all containers"
	@echo "  make clean      Clean up containers and volumes"
	@echo "  make test       Test the API with curl"
	@echo "  make logs       Show Valkey logs"

install:
	pipenv install

run:
	@chmod +x run-local.sh
	@./run-local.sh

stop:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf __pycache__ .pytest_cache

test:
	@echo "Testing health endpoint..."
	@curl -s http://localhost:8000/api/v1/health | jq
	@echo ""
	@echo "Testing links endpoint..."
	@curl -s http://localhost:8000/api/v1/applications/taco-backend-prod/links \
		-H "Argocd-Application-Name: nonprod:taco-backend-prod" | jq

logs:
	docker-compose logs -f valkey
