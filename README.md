# Paper Scope

Paper Scope is a research intelligence platform that automatically collects trending papers from sources such as Hugging Face Papers and arXiv, enriches them with LLM-generated summaries, and builds an evolving knowledge graph that reveals relationships within and across publications. The system is designed to run fully on-premise with podman-compose while remaining configurable for cloud-hosted services.

## Key Features

- **Automated Trend Monitoring** – Daily scheduled crawler that ingests trending research papers and stores PDFs in a persistent volume.
- **On-Demand Harvesting** – Manual execution from the Streamlit UI to trigger immediate crawling and enrichment.
- **Flexible LLM Selection** – Choose between a locally hosted Ollama model or OpenAI-hosted models via configuration.
- **Knowledge Graph Construction** – Persist structured insights into Neo4j to explore entities, relationships, and inter-paper links.
- **Interactive Research Workspace** – Streamlit frontend to read PDFs, explore semantic graphs, and visualize cross-paper connections.
- **Extensible Notifications** – Architecture-ready for future email notifications about paper updates or graph changes.

## High-Level Architecture

```
┌──────────────┐        ┌─────────────┐        ┌──────────────┐
│ Streamlit UI │◀──────▶│  FastAPI    │◀──────▶│  Neo4j Graph │
│ (frontend)   │  REST  │  backend    │  Bolt  │    Database  │
└─────▲────────┘        │             │        └──────────────┘
      │                 │   ┌─────────▼─────────┐
      │   WebSocket     │   │ Scheduler / Worker │
      │  updates        │   │  (APScheduler)     │
      │                 └───┴─────────▲─────────┘
      │                         ingest │
      │   PDF streaming / graph data   │
┌─────┴────────┐                 ┌─────┴──────────┐
│   Nginx      │  Reverse proxy  │ Storage Volume │
│ (TLS/static) │────────────────▶│  (PDF files)   │
└──────────────┘                 └────────────────┘
```

- **Nginx** serves Streamlit, proxies API requests to FastAPI, and exposes static PDF assets.
- **FastAPI backend** hosts REST endpoints, orchestrates crawlers, LLM enrichment, and graph persistence.
- **Scheduler worker** (APScheduler) runs in the backend container to trigger the daily ingestion job.
- **Streamlit frontend** provides interactive views for triggering ingestions, browsing PDFs, and exploring graphs.
- **Neo4j** stores paper metadata, entities, relationships, and cross-paper connections.
- **Shared volume** persists downloaded PDFs and enrichment outputs.

## Repository Layout (Planned)

```
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers
│   │   ├── core/             # config, logging, settings
│   │   ├── services/         # crawling, parsing, LLM, graph ingestion
│   │   ├── workers/          # scheduler jobs
│   │   └── schemas/          # pydantic models
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── app.py                # Streamlit entry point
│   ├── components/           # custom visualization components
│   └── requirements.txt
├── infra/
│   ├── podman-compose.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── neo4j/
│       └── conf/
├── scripts/                  # CLI utilities for manual ingestion, seeding, etc.
├── README.md
├── PLANS.md
└── AGENTS.md
```

## Data Flow

1. **Trend Discovery** – Crawler fetches trending lists (e.g., Hugging Face Papers trending endpoint) and resolves to arXiv/official URLs.
2. **Metadata Extraction** – Parse titles, authors, abstracts, categories, and fetch the PDF.
3. **Storage** – Save PDFs into a versioned directory inside the shared volume (`/data/papers/<source>/<year>/<id>.pdf`).
4. **LLM Enrichment** – Generate summaries, key concepts, entities, and relationship triples using the configured LLM provider.
5. **Graph Update** – Upsert nodes/relationships in Neo4j representing papers, authors, topics, and cross-references.
6. **Frontend Presentation** – Streamlit pulls graph data via REST APIs and renders:
   - PDF viewer (embedded via `streamlit-pdf-viewer` or custom component)
   - Knowledge graph visualization (e.g., via `pyvis` or `plotly`)
   - Cross-paper relationship explorer.

## Configuration & Deployment

1. **Environment Variables**

   Runtime configuration for the backend is loaded from a `.env` file in the
   repository root. An example is provided as `.env.example`—copy it and update
   the values before starting the services:

   ```bash
   cp .env.example .env
   ```

   | Variable | Description |
   | --- | --- |
  | `PAPER_SCOPE_STORAGE_ROOT` | Filesystem path mounted inside the backend container where PDFs and metadata are persisted. Defaults to `/data/papers`. |
  | `PAPER_SCOPE_LLM_PROVIDER` | Select the enrichment backend (`mock`, `ollama`, or `openai`). Defaults to `mock`. |
  | `PAPER_SCOPE_OPENAI_API_KEY` | Required when enabling OpenAI-powered enrichment workflows. Leave blank to disable features that depend on OpenAI. |
  | `PAPER_SCOPE_OLLAMA_BASE_URL` | Base URL for the Ollama server when using the local provider. |
  | `PAPER_SCOPE_OLLAMA_MODEL` | Ollama model name to request for enrichment. |
  | `PAPER_SCOPE_NEO4J_PASSWORD` | Neo4j authentication password (minimum 8 characters). Defaults to `changeme123`. |
  | `PAPER_SCOPE_BACKEND_URL` | Base URL the frontend uses to call the backend API. Defaults to `http://backend:8000/api` for container workflows. |
  | `PAPER_SCOPE_BACKEND_PUBLIC_URL` | Public URL served to browsers for API access. Defaults to `/api`, set to `http://localhost:8080/api` when bypassing nginx. |
  | `PAPER_SCOPE_SCHEDULER_TIMEZONE` | Optional override for the APScheduler timezone (defaults to `UTC`). |

   Additional integrations (Neo4j connection, crawler configuration, etc.) will
   introduce more environment switches as those features are implemented. Each
   new variable will be documented in the example file.

2. **Podman Compose Services**
   - `frontend`: Streamlit app served via Nginx upstream.
   - `backend`: FastAPI app with scheduler, uses Python 3.11-slim image.
   - `nginx`: Reverse proxy container exposing port 443/80 with TLS termination.
   - `neo4j`: Official Neo4j container with mounted data and config volumes.
   - External dependency: Start Ollama locally (outside the compose stack) when
     selecting the Ollama provider. The default base URL
     `http://host.containers.internal:11434` points to the host bridge from
     containers; switch to `http://localhost:11434` if you run the backend
     directly on your machine.
   - PDF assets are written to `storage/papers/` on the host (bind-mounted into
     the backend container at `/data/papers`). Each ingestion stores files under
     `<source>/<year>/<paper_id>/` so you can inspect downloaded PDFs directly
     from the repository checkout.

3. **Volumes**
   - `neo4j-data`, `neo4j-logs` for Neo4j persistence.

## Development Workflow

### Prerequisites

- Podman with the `podman-compose` plugin (or Docker Compose; see notes below)
- Optional: Python 3.11 and [Poetry](https://python-poetry.org/) if you prefer to run the backend without containers.
- Ensure the `storage/papers/` directory exists (a `.gitkeep` placeholder is
  provided) so PDFs can be inspected locally when the stack is running.

### Using the Makefile

Common development actions are wrapped in a top-level `Makefile`:

```bash
# Build backend and frontend images (installs dependencies inside containers)
make install-all

# Run the FastAPI backend (attached; press Ctrl+C to stop)
make backend-dev

# Launch the Streamlit frontend (starts backend automatically via depends_on)
make frontend-dev

# Execute backend unit tests inside the backend container
make backend-test

# Start the full stack (frontend, backend, Nginx, Neo4j, etc.) via podman-compose
make compose-up

# Stop the running compose stack
make compose-down
```

Pass a different compose runner by overriding `PODMAN_COMPOSE`. For example, to use Docker Compose:

```bash
make compose-up PODMAN_COMPOSE="docker compose"
```

### Manual Workflow

1. Clone the repository and build the service images (via `make install-all`).
2. Use `make compose-up` to start services locally or run `make backend-dev`/`make frontend-dev` for individual components.
3. Access the UI at `http://localhost:8080/` when running the full stack behind Nginx, or use the direct service URLs when running components individually (`http://localhost:8501` for Streamlit, `http://localhost:8000/api/health` for the backend).
4. Run backend unit tests with `make backend-test`.
5. Use `scripts/run_ingest.py --once` for manual ingestion during development.

## Future Enhancements

- Email notification service that watches for updates to tracked papers or significant graph changes.
- User accounts and personalization (watchlists, saved searches).
- Advanced search leveraging vector embeddings and similarity queries in Neo4j.
- Incremental ingestion of citations and references to expand the knowledge graph beyond trending lists.
- Integration with document QA agents for interactive paper questioning.

## License

This project will adopt an MIT License unless specified otherwise by project stakeholders.
