.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# Project directories
PYTHON_DIR := src/multi-agent-hr-assistant
UI_DIR := src/multi-agent-hr-assistant/ui
TESTS_DIR := tests

help:
	@echo "Multi-Agent HR Assistant - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install              - Install all dependencies (Python backend + UI)"
	@echo "  make install-backend      - Install Python backend dependencies"
	@echo "  make install-ui           - Install UI dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev                  - Run backend development server"
	@echo "  make dev-ui               - Run UI development server"
	@echo "  make dev-all              - Run both backend and UI (requires tmux or multiple terminals)"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test                 - Run all tests"
	@echo "  make test-cov             - Run tests with coverage report"
	@echo "  make lint                 - Run linting checks"
	@echo "  make format               - Format Python code"
	@echo "  make format-check         - Check if code needs formatting"
	@echo ""
	@echo "Docker & Deployment:"
	@echo "  make docker-build         - Build Docker images"
	@echo "  make docker-up            - Start Docker containers"
	@echo "  make docker-down          - Stop Docker containers"
	@echo "  make docker-logs          - View Docker container logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean                - Clean up temporary files and caches"
	@echo "  make requirements          - Generate requirements.txt from pyproject.toml"

#==============================================================================
# Installation
#==============================================================================

install: install-backend install-ui
	@echo "✓ All dependencies installed successfully"

install-backend:
	@echo "Installing backend dependencies..."
	pip install -e .
	pip install -r tests/requirements-test.txt
	@echo "✓ Backend dependencies installed"

install-ui:
	@echo "Installing UI dependencies..."
	cd $(UI_DIR) && npm install
	@echo "✓ UI dependencies installed"

#==============================================================================
# Development
#==============================================================================

dev:
	@echo "Starting backend development server..."
	@echo "Server will be available at http://localhost:8000"
	cd $(PYTHON_DIR) && uvicorn main:combined_app --host 0.0.0.0 --port 8000 --reload

dev-ui:
	@echo "Starting UI development server..."
	@echo "UI will be available at http://localhost:3000"
	cd $(UI_DIR) && npm run dev

dev-all:
	@echo "To run both servers, open two terminals and run:"
	@echo "  Terminal 1: make dev"
	@echo "  Terminal 2: make dev-ui"

#==============================================================================
# Testing & Quality
#==============================================================================

test:
	@echo "Running tests..."
	cd $(TESTS_DIR) && python run_tests.py
	@echo "✓ Tests completed"

test-cov:
	@echo "Running tests with coverage..."
	cd $(TESTS_DIR) && pytest --cov=../src/multi-agent-hr-assistant --cov-report=html --cov-report=term-missing
	@echo "✓ Coverage report generated (see htmlcov/index.html)"

lint:
	@echo "Running linting checks..."
	pylint $(PYTHON_DIR)/application $(PYTHON_DIR)/domain $(PYTHON_DIR)/infrastructure
	@echo "✓ Linting completed"

format:
	@echo "Formatting Python code..."
	black $(PYTHON_DIR) $(TESTS_DIR)
	isort $(PYTHON_DIR) $(TESTS_DIR)
	@echo "✓ Code formatted"

format-check:
	@echo "Checking code formatting..."
	black --check $(PYTHON_DIR) $(TESTS_DIR)
	isort --check-only $(PYTHON_DIR) $(TESTS_DIR)

#==============================================================================
# Docker
#==============================================================================

docker-build:
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ Docker images built"

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d
	@echo "✓ Containers started"
	@echo "  - Backend API: http://localhost:8000"
	@echo "  - Redis: localhost:6379"

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down
	@echo "✓ Containers stopped"

docker-logs:
	docker-compose logs -f

docker-clean:
	@echo "Cleaning Docker resources..."
	docker-compose down -v
	@echo "✓ Docker resources cleaned"

#==============================================================================
# Utilities
#==============================================================================

clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleanup completed"

requirements:
	@echo "Generating requirements.txt..."
	pip install pip-tools
	pip-compile pyproject.toml -o requirements.txt
	@echo "✓ requirements.txt generated"

.DEFAULT_GOAL := help
