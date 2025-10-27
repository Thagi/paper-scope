# Paper Scope – Implementation Guidelines for Coding Assistants

These instructions apply to the entire repository unless superseded by nested `AGENTS.md` files.

## General Principles
- Target **Python 3.11** for backend services and utility scripts.
- Prefer **type annotations** everywhere. Use `mypy`-friendly typing and `from __future__ import annotations` in Python packages.
- Follow **Black** formatting (line length 88) and **isort** import ordering with the "black" profile.
- Write docstrings for all public functions, classes, and FastAPI endpoints using Google-style docstrings.
- Avoid introducing global state. Use dependency injection (FastAPI Depends, configuration objects) for services.
- Never wrap import statements in try/except blocks.
- Keep functions focused: if exceeding ~40 lines or multiple responsibilities, refactor.

## Backend (FastAPI)
- Place API routers under `backend/app/api/`. Organize by resource (`papers.py`, `graphs.py`, etc.).
- Configuration belongs in `backend/app/core/settings.py` using `pydantic-settings`.
- Long-running jobs (crawlers, LLM enrichment) should live in `backend/app/services/` and expose async interfaces when they interact with I/O.
- Scheduler logic should use APScheduler, configured in `backend/app/workers/scheduler.py`.
- For Neo4j access, wrap the official Python driver in repository classes under `backend/app/services/graph/` and expose transactional helper methods. Use `neo4j.AsyncGraphDatabase` for async operations.
- Provide unit tests under `backend/tests/` using `pytest` with `pytest-asyncio` for async code.

## Frontend (Streamlit)
- The main app entry is `frontend/app.py`. Modularize UI sections under `frontend/components/` with helper functions returning Streamlit elements.
- Use `st.cache_data` or `st.cache_resource` judiciously for expensive operations (graph queries, PDF fetches).
- Custom visualizations (knowledge graph, cross-paper network) should leverage reusable helper modules under `frontend/components/graphs.py` etc.

## Infrastructure & Tooling
- Podman compose definitions go under `infra/podman-compose.yml`.
- Provide environment templates (`.env.example`) in the repo root if new configuration options are added.
- Scripts should live in `scripts/` and use `typer` for CLI ergonomics.

## Testing & CI
- Add GitHub Actions workflows under `.github/workflows/` when CI is introduced. Use separate jobs for backend (pytest, mypy) and frontend (linting, smoke tests).
- Ensure every new feature includes at least one automated test or explain why not in the PR description.

## Documentation
- Update `README.md` with major architectural changes or setup steps.
- Maintain `PLANS.md` when architectural decisions significantly shift.
