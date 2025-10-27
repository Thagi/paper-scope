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
   - `LLM_PROVIDER` (`ollama` or `openai`)
   - `OLLAMA_MODEL` / `OPENAI_MODEL`
   - `OPENAI_API_KEY` (if using OpenAI)
   - `TREND_SOURCES` (comma-separated list of crawler modules to activate)
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
   - `SCHEDULER_CRON` (e.g., `0 3 * * *`)

2. **Podman Compose Services**
   - `frontend`: Streamlit app served via Nginx upstream.
   - `backend`: FastAPI app with scheduler, uses Python 3.11-slim image.
   - `nginx`: Reverse proxy container exposing port 443/80 with TLS termination.
   - `neo4j`: Official Neo4j container with mounted data and config volumes.
   - `ollama` (optional): Ollama server for local LLMs.

3. **Volumes**
   - `paper-data`: Persist downloaded PDFs and enrichment metadata.
   - `neo4j-data`, `neo4j-logs`.

## Development Workflow

1. Clone the repository and install dev dependencies for backend and frontend.
2. Use `podman-compose up --build` to start services locally.
3. Access the UI at `https://localhost/` (Nginx handles routing to Streamlit and FastAPI).
4. Run backend unit tests with `poetry run pytest` (backend) and `pytest` or `streamlit` checks for frontend components.
5. Use `scripts/run_ingest.py --once` for manual ingestion during development.

## Future Enhancements

- Email notification service that watches for updates to tracked papers or significant graph changes.
- User accounts and personalization (watchlists, saved searches).
- Advanced search leveraging vector embeddings and similarity queries in Neo4j.
- Incremental ingestion of citations and references to expand the knowledge graph beyond trending lists.
- Integration with document QA agents for interactive paper questioning.

## License

This project will adopt an MIT License unless specified otherwise by project stakeholders.
