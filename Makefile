.PHONY: help install install-dev test lint format clean run-backend run-frontend docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       - Install production dependencies"
	@echo "  make install-dev   - Install development dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make run-backend   - Run backend server"
	@echo "  make run-frontend  - Run frontend dev server"
	@echo "  make docker-up     - Start with Docker Compose"
	@echo "  make docker-down   - Stop Docker Compose"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=src/adk_agentic_writer

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff check --fix src/ tests/
	black src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache

run-backend:
	uvicorn src.adk_agentic_writer.backend.api:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm start

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
