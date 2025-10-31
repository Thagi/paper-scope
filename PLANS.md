# Paper Scope Implementation Plan

This document outlines the phased roadmap for building the Paper Scope platform.

## Status Update

- **Phase 0** baseline scaffolding is complete (FastAPI + Streamlit skeleton with health checks).
- **Phase 1** initial ingestion pipeline implemented with Hugging Face trending crawler, PDF downloader, Neo4j persistence, and manual trigger endpoint.
- **Phase 2** core LLM enrichment abstraction delivered with mock, Ollama, and OpenAI providers plus Neo4j graph updates.
- **Phase 3** Streamlit UI now renders PDF workspace, ingestion dashboard, and graph visualizations backed by live API data.

## Phase 0 – Repository Bootstrap
- Scaffold backend (`backend/app`) with FastAPI skeleton, configuration, and health endpoint.
- Initialize Streamlit app with placeholder pages for ingestion controls, PDF viewer, and graph dashboards.
- Set up shared tooling: `poetry` for backend, `requirements.txt` for frontend, `pre-commit` hooks (black, isort, mypy, pytest).
- Create `infra/podman-compose.yml` with services (backend, frontend, nginx, neo4j) and shared volumes, documenting Ollama as an external dependency when needed.

## Phase 1 – Data Ingestion Pipeline
1. **Source Connectors**
   - Implement modular crawler interfaces for Hugging Face Papers trending and arXiv (RSS / API).
   - Normalize metadata into internal `PaperRecord` schema.
2. **PDF Downloader**
   - Reliable download with retry/backoff, checksum validation, and storage under `/data/papers/<source>/<year>/<paper_id>.pdf`.
   - Maintain metadata manifest (JSON) alongside PDFs.
3. **Scheduler Integration**
   - APScheduler cron job running daily inside backend container.
   - Manual trigger endpoint (`POST /ingest/run`) to enqueue ingestion via UI.

## Phase 2 – LLM Enrichment & Knowledge Graph
1. **LLM Abstraction Layer**
   - Define `LLMClient` protocol with implementations for Ollama (local HTTP API) and OpenAI.
   - Config-driven selection with graceful fallback and rate-limit handling.
2. **Enrichment Pipeline**
   - Generate: summary, key bullet highlights, named entities, relationship triples, suggested tags.
   - Persist enrichment metadata (JSON) per paper.
3. **Neo4j Persistence**
   - Design graph schema: `Paper`, `Author`, `Concept`, `Relation` nodes with relationships (`AUTHORED_BY`, `MENTIONS`, `RELATES_TO`).
   - Implement transactional upsert logic and maintain ingestion checkpoints.

## Phase 3 – Frontend Experience
1. **Dashboard Layout**
   - Landing page with ingestion controls (status, last run, manual trigger button) and trend insights.
2. **PDF Workspace**
   - Embedded PDF viewer with metadata sidebar and LLM summary display.
3. **Knowledge Graph Visualization**
   - Interactive graph (pyvis/plotly) showing intra-paper concepts and cross-paper links.
   - Filters for source, topic, time range.
4. **Search & Browsing**
   - Search bar for titles/authors; list view of ingested papers with tags.

## Phase 3a – UX Enhancements (In Progress)
- Add a Library Insights panel surfacing coverage metrics (tags, summaries, PDFs) to highlight ingestion completeness.
- Provide trend visualisations for top tags and publication timelines to quickly gauge topical focus.
- Iteratively expand quick actions in the paper browser (e.g., saved filters, bulk tagging) based on user feedback.

## Phase 4 – Notifications & Extensions
- Implement change detection (new versions, new connections) and queue email notifications (via SMTP / third-party).
- Add user preferences for notification subscriptions.
- Explore incremental ingestion of citations and references for deeper graph coverage.

## Cross-Cutting Concerns
- Observability: structured logging, metrics (Prometheus endpoints) for ingestion throughput and LLM usage.
- Error handling: dead-letter queue or retry mechanism for failed ingestion steps.
- Security: API authentication for manual triggers, secure secrets management for API keys.
- Documentation: keep README, architecture diagrams, and API references up to date.
