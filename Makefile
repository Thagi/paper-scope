# Makefile for Paper Scope project automation

PODMAN_COMPOSE ?= podman-compose
COMPOSE_FILE ?= infra/podman-compose.yml
BACKEND_SERVICE := backend
FRONTEND_SERVICE := frontend
BACKEND_DIR := backend
FRONTEND_DIR := frontend

BACKEND_RUN := $(PODMAN_COMPOSE) -f $(COMPOSE_FILE) run --rm $(BACKEND_SERVICE)
FRONTEND_RUN := $(PODMAN_COMPOSE) -f $(COMPOSE_FILE) run --rm $(FRONTEND_SERVICE)

.PHONY: help install-backend install-frontend install-all backend-dev backend-test frontend-dev compose-up compose-down compose-logs format-backend format-frontend lint-backend clean

help:
	@echo "Paper Scope helper targets (container-native workflow)"
	@echo "  make install-backend   Build the backend image and install dependencies"
	@echo "  make install-frontend  Build the frontend image and install dependencies"
	@echo "  make install-all       Build backend and frontend images"
	@echo "  make backend-dev       Run the FastAPI backend via podman-compose"
	@echo "  make frontend-dev      Run the Streamlit frontend via podman-compose"
	@echo "  make backend-test      Execute backend pytest suite inside the container"
	@echo "  make format-backend    Format backend Python code inside the container"
	@echo "  make format-frontend   Format frontend Python code inside the container"
	@echo "  make compose-up        Build and start the full stack via podman-compose"
	@echo "  make compose-down      Stop the podman-compose stack"
	@echo "  make compose-logs      Tail logs from the compose stack"

install-backend:
	$(PODMAN_COMPOSE) -f $(COMPOSE_FILE) build $(BACKEND_SERVICE)

install-frontend:
	$(PODMAN_COMPOSE) -f $(COMPOSE_FILE) build $(FRONTEND_SERVICE)

install-all: install-backend install-frontend

backend-dev:
	$(PODMAN_COMPOSE) -f $(COMPOSE_FILE) up $(BACKEND_SERVICE)

frontend-dev:
	$(PODMAN_COMPOSE) -f $(COMPOSE_FILE) up $(FRONTEND_SERVICE)

backend-test:
	$(BACKEND_RUN) poetry run pytest

format-backend:
	$(BACKEND_RUN) poetry run isort app tests
	$(BACKEND_RUN) poetry run black app tests

format-frontend:
	$(FRONTEND_RUN) black frontend

lint-backend:
	$(BACKEND_RUN) poetry run black --check app tests
	$(BACKEND_RUN) poetry run isort --check-only app tests

compose-up:
	$(PODMAN_COMPOSE) -f $(COMPOSE_FILE) up --build -d

compose-down:
	$(PODMAN_COMPOSE) -f $(COMPOSE_FILE) down

compose-logs:
	$(PODMAN_COMPOSE) -f $(COMPOSE_FILE) logs -f

clean:
	rm -rf $(BACKEND_DIR)/.pytest_cache $(BACKEND_DIR)/.mypy_cache $(FRONTEND_DIR)/__pycache__
