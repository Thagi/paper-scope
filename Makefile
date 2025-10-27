# Makefile for Paper Scope project automation

PYTHON ?= python3.11
POETRY ?= poetry
PODMAN_COMPOSE ?= podman-compose
BACKEND_DIR := backend
FRONTEND_DIR := frontend

.PHONY: help install-backend install-frontend install-all backend-dev backend-test frontend-dev compose-up compose-down compose-logs format-backend format-frontend lint-backend clean

help:
@echo "Paper Scope helper targets"
@echo "  make install-backend   Install backend dependencies with poetry"
@echo "  make install-frontend  Install frontend dependencies via pip"
@echo "  make install-all       Install dependencies for both backend and frontend"
@echo "  make backend-dev       Run the FastAPI backend with uvicorn"
@echo "  make frontend-dev      Run the Streamlit frontend app"
@echo "  make backend-test      Execute backend pytest suite"
@echo "  make format-backend    Format backend Python code with black & isort"
@echo "  make format-frontend   Format frontend Python code with black"
@echo "  make compose-up        Build and start the full stack via podman-compose"
@echo "  make compose-down      Stop the podman-compose stack"
@echo "  make compose-logs      Tail logs from the compose stack"

install-backend:
cd $(BACKEND_DIR) && $(POETRY) install

install-frontend:
$(PYTHON) -m pip install --upgrade pip
$(PYTHON) -m pip install -r $(FRONTEND_DIR)/requirements.txt black

install-all: install-backend install-frontend

backend-dev:
cd $(BACKEND_DIR) && $(POETRY) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
cd $(FRONTEND_DIR) && streamlit run app.py --server.port 8501 --server.address 0.0.0.0

backend-test:
cd $(BACKEND_DIR) && $(POETRY) run pytest

format-backend:
cd $(BACKEND_DIR) && $(POETRY) run isort app tests && $(POETRY) run black app tests

format-frontend:
cd $(FRONTEND_DIR) && black .

lint-backend:
cd $(BACKEND_DIR) && $(POETRY) run black --check app tests && $(POETRY) run isort --check-only app tests

compose-up:
$(PODMAN_COMPOSE) -f infra/podman-compose.yml up --build -d

compose-down:
$(PODMAN_COMPOSE) -f infra/podman-compose.yml down

compose-logs:
$(PODMAN_COMPOSE) -f infra/podman-compose.yml logs -f

clean:
rm -rf $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/.mypy_cache $(FRONTEND_DIR)/__pycache__
