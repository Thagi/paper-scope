"""Neo4j repository utilities."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import re
from pathlib import Path
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.time import DateTime as Neo4jDateTime

_NORMALIZE_PATTERN = re.compile(r"[^a-z0-9]+")

from backend.app.schemas import (
    GraphEdge,
    GraphNode,
    LLMAnalysis,
    PaperGraph,
    PaperRecord,
    StoredPaper,
)


class Neo4jGraphRepository:
    """Repository encapsulating Neo4j interactions."""

    def __init__(self, driver: AsyncDriver) -> None:
        self._driver = driver

    @classmethod
    def from_settings(
        cls, uri: str, user: str, password: str
    ) -> "Neo4jGraphRepository":
        driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        return cls(driver)

    async def close(self) -> None:
        await self._driver.close()

    async def ensure_constraints(self) -> None:
        async with self._driver.session() as session:
            await session.execute_write(
                lambda tx: tx.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Paper) REQUIRE p.external_id IS UNIQUE"
                )
            )
            await session.execute_write(
                lambda tx: tx.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.normalized_name IS UNIQUE"
                )
            )
            await session.execute_write(
                lambda tx: tx.run(
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE"
                )
            )

    async def paper_exists(self, external_id: str) -> bool:
        async with self._driver.session() as session:
            return await session.execute_read(
                self._paper_exists_tx, external_id=external_id
            )

    async def upsert_paper(
        self,
        record: PaperRecord,
        analysis: LLMAnalysis,
        *,
        storage_path: Path,
    ) -> None:
        async with self._driver.session() as session:
            record_payload = record.model_dump()
            pdf_url = record_payload.get("pdf_url")
            if pdf_url is not None:
                record_payload["pdf_url"] = str(pdf_url)
            landing_url = record_payload.get("landing_url")
            if landing_url is not None:
                record_payload["landing_url"] = str(landing_url)

            analysis_payload = analysis.model_dump()
            for concept in analysis_payload.get("concepts", []):
                name = concept.get("name")
                if name:
                    concept["normalized_name"] = self._normalize_concept_name(name)
            for rel in analysis_payload.get("relationships", []):
                target = rel.get("target")
                if target:
                    rel["target_display"] = target
                    rel["target_normalized"] = self._normalize_concept_name(target)
                    rel.setdefault("relation", "RELATED")

            await session.execute_write(
                self._upsert_paper_tx,
                record=record_payload,
                analysis=analysis_payload,
                storage_path=str(storage_path),
            )

    async def get_recent_papers(self, limit: int) -> list[StoredPaper]:
        async with self._driver.session() as session:
            return await session.execute_read(self._get_recent_papers_tx, limit=limit)

    async def get_paper(self, external_id: str) -> StoredPaper | None:
        async with self._driver.session() as session:
            return await session.execute_read(
                self._get_paper_tx, external_id=external_id
            )

    async def get_paper_graph(self, external_id: str) -> PaperGraph:
        async with self._driver.session() as session:
            return await session.execute_read(
                self._get_paper_graph_tx, external_id=external_id
            )

    async def get_paper_network(self, limit: int) -> PaperGraph:
        async with self._driver.session() as session:
            return await session.execute_read(self._get_paper_network_tx, limit=limit)

    @staticmethod
    async def _paper_exists_tx(tx, *, external_id: str) -> bool:
        result = await tx.run(
            "MATCH (p:Paper {external_id: $external_id}) RETURN count(p) > 0 AS exists",
            external_id=external_id,
        )
        record = await result.single()
        return bool(record and record["exists"])

    @staticmethod
    async def _get_recent_papers_tx(tx, *, limit: int) -> list[StoredPaper]:
        result = await tx.run(
            """
            MATCH (p:Paper)
            RETURN p
            ORDER BY coalesce(p.published_at, datetime({epochseconds: 0})) DESC,
                     coalesce(p.created_at, datetime({epochseconds: 0})) DESC
            LIMIT $limit
            """,
            limit=limit,
        )
        papers: list[StoredPaper] = []
        async for record in result:
            node = record["p"]
            papers.append(
                StoredPaper(
                    paper_id=node["external_id"],
                    title=node.get("title", "Untitled"),
                    source=node.get("source"),
                    summary=node.get("summary"),
                    landing_url=node.get("landing_url"),
                    tags=node.get("tags", []),
                    authors=node.get("authors", []),
                    published_at=Neo4jGraphRepository._coerce_datetime(
                        node.get("published_at")
                    ),
                    storage_path=Path(node.get("storage_path"))
                    if node.get("storage_path")
                    else None,
                    key_points=node.get("key_points", []),
                )
            )
        return papers

    @staticmethod
    async def _get_paper_tx(tx, *, external_id: str) -> StoredPaper | None:
        result = await tx.run(
            "MATCH (p:Paper {external_id: $external_id}) RETURN p",
            external_id=external_id,
        )
        record = await result.single()
        if not record:
            return None
        node = record["p"]
        return StoredPaper(
            paper_id=node["external_id"],
            title=node.get("title", "Untitled"),
            source=node.get("source"),
            summary=node.get("summary"),
            landing_url=node.get("landing_url"),
            tags=node.get("tags", []),
            authors=node.get("authors", []),
            published_at=Neo4jGraphRepository._coerce_datetime(
                node.get("published_at")
            ),
            storage_path=Path(node.get("storage_path"))
            if node.get("storage_path")
            else None,
            key_points=node.get("key_points", []),
        )

    @staticmethod
    async def _get_paper_graph_tx(tx, *, external_id: str) -> PaperGraph:
        result = await tx.run(
            """
            MATCH (p:Paper {external_id: $external_id})
            OPTIONAL MATCH (p)-[r]->(n)
            RETURN p, collect(DISTINCT r) AS rels, collect(DISTINCT n) AS nodes
            """,
            external_id=external_id,
        )
        record = await result.single()
        if not record:
            return PaperGraph(nodes=[], edges=[])

        paper_node = record["p"]
        related_nodes = [node for node in record["nodes"] if node]
        relationships = [rel for rel in record["rels"] if rel]

        element_to_graph_id: dict[str, str] = {}
        node_map: dict[str, GraphNode] = {}

        element_id, graph_node = Neo4jGraphRepository._graph_node_from_record(
            paper_node
        )
        element_to_graph_id[element_id] = graph_node.id
        node_map[graph_node.id] = graph_node

        for node in related_nodes:
            element_id, graph_node = Neo4jGraphRepository._graph_node_from_record(node)
            element_to_graph_id[element_id] = graph_node.id
            node_map.setdefault(graph_node.id, graph_node)

        edges: list[GraphEdge] = []
        for rel in relationships:
            source_id = element_to_graph_id.get(rel.start_node.element_id)
            target_id = element_to_graph_id.get(rel.end_node.element_id)
            if not source_id or not target_id:
                continue
            metadata = Neo4jGraphRepository._clean_metadata(dict(rel))
            edges.append(
                GraphEdge(
                    id=rel.element_id,
                    source=source_id,
                    target=target_id,
                    type=rel.type,
                    metadata=metadata,
                )
            )
        return PaperGraph(nodes=list(node_map.values()), edges=edges)

    @staticmethod
    async def _get_paper_network_tx(tx, *, limit: int) -> PaperGraph:
        result = await tx.run(
            """
            MATCH (p:Paper)-[r:RELATES_TO]->(c:Concept)<-[r2:RELATES_TO]-(other:Paper)
            WHERE p.external_id <> other.external_id
            RETURN p, r, r2, c, other
            LIMIT $limit
            """,
            limit=limit,
        )
        element_to_graph_id: dict[str, str] = {}
        node_map: dict[str, GraphNode] = {}
        concept_edges: dict[tuple[str, str], dict[str, Any]] = {}
        pair_concepts: defaultdict[tuple[str, str], set[str]] = defaultdict(set)

        async for record in result:
            paper = record["p"]
            other = record["other"]
            concept = record["c"]
            rel = record["r"]
            rel_other = record["r2"]

            for node in (paper, other, concept):
                element_id, graph_node = Neo4jGraphRepository._graph_node_from_record(
                    node
                )
                element_to_graph_id[element_id] = graph_node.id
                node_map.setdefault(graph_node.id, graph_node)

            paper_id = element_to_graph_id.get(paper.element_id)
            other_id = element_to_graph_id.get(other.element_id)
            concept_id = element_to_graph_id.get(concept.element_id)

            if paper_id and concept_id:
                key = (paper_id, concept_id)
                payload = concept_edges.setdefault(
                    key,
                    {
                        "source": paper_id,
                        "target": concept_id,
                        "relations": set(),
                    },
                )
                payload["relations"].add(dict(rel).get("relation") or rel.type)

            if other_id and concept_id:
                key = (other_id, concept_id)
                payload = concept_edges.setdefault(
                    key,
                    {
                        "source": other_id,
                        "target": concept_id,
                        "relations": set(),
                    },
                )
                relation_value = None
                if rel_other is not None:
                    relation_value = dict(rel_other).get("relation") or rel_other.type
                payload["relations"].add(relation_value or "RELATES_TO")

            if paper_id and other_id and concept_id:
                concept_node = node_map.get(concept_id)
                concept_label = concept_node.label if concept_node else concept_id
                pair_key = tuple(sorted((paper_id, other_id)))
                pair_concepts[pair_key].add(concept_label)

        edges: list[GraphEdge] = []
        for payload in concept_edges.values():
            relations = sorted(rel for rel in payload["relations"] if rel)
            metadata: dict[str, Any] = {}
            if relations:
                metadata["relations"] = relations
            edges.append(
                GraphEdge(
                    id=f"{payload['source']}->{payload['target']}",
                    source=payload["source"],
                    target=payload["target"],
                    type="RELATES_TO",
                    metadata=metadata,
                )
            )

        for (paper_id, other_id), shared_concepts in pair_concepts.items():
            metadata = {
                "shared_concepts": sorted(shared_concepts),
                "weight": len(shared_concepts),
            }
            edges.append(
                GraphEdge(
                    id=f"{paper_id}:::{other_id}",
                    source=paper_id,
                    target=other_id,
                    type="SHARES_CONCEPT",
                    metadata=metadata,
                )
            )

        return PaperGraph(nodes=list(node_map.values()), edges=edges)

    @staticmethod
    async def _upsert_paper_tx(
        tx, *, record: dict, analysis: dict, storage_path: str
    ) -> None:
        await (
            await tx.run(
                """
            MERGE (p:Paper {external_id: $record.external_id})
            SET p.title = $record.title,
                p.abstract = $record.abstract,
                p.source = $record.source,
                p.authors = $record.authors,
                p.landing_url = $record.landing_url,
                p.tags = $record.tags,
                p.published_at = $record.published_at,
                p.summary = $analysis.summary,
                p.key_points = $analysis.key_points,
                p.storage_path = $storage_path,
                p.updated_at = datetime(),
                p.created_at = coalesce(p.created_at, datetime())
            WITH p, $record.authors AS authors
            UNWIND authors AS author
            WITH p, author
            MERGE (a:Author {name: author})
            MERGE (p)-[:AUTHORED_BY]->(a)
            WITH DISTINCT p
            OPTIONAL MATCH (p)-[old:RELATES_TO]->(:Concept)
            DELETE old
            WITH DISTINCT p, $analysis AS analysis
            UNWIND analysis.concepts AS concept
            WITH p, concept
            WHERE coalesce(concept.normalized_name, "") <> ""
            MERGE (c:Concept {normalized_name: concept.normalized_name})
            SET c.name = coalesce(concept.name, c.name),
                c.description = coalesce(concept.description, c.description)
            MERGE (p)-[:RELATES_TO {relation: 'TAG'}]->(c)
            WITH DISTINCT p, $analysis.relationships AS rels
            UNWIND rels AS rel
            WITH p, rel
            WHERE coalesce(rel.target_normalized, "") <> ""
            MERGE (target:Concept {normalized_name: rel.target_normalized})
            SET target.name = coalesce(rel.target_display, target.name)
            MERGE (p)-[r:RELATES_TO {relation: coalesce(rel.relation, 'RELATED')}]->(target)
            SET r.source = rel.source
            """,
                record=record,
                analysis=analysis,
                storage_path=storage_path,
            )
        ).consume()

    @staticmethod
    def _normalize_concept_name(name: str) -> str:
        slug = _NORMALIZE_PATTERN.sub("-", name.lower()).strip("-")
        return slug or name.lower()

    @staticmethod
    def _graph_node_from_record(node) -> tuple[str, GraphNode]:  # type: ignore[no-untyped-def]
        labels = {label for label in getattr(node, "labels", [])}
        node_type = "Entity"
        node_id = node.get("external_id") or node.get("name") or node.element_id
        label = node.get("title") or node.get("name") or node_id
        metadata: dict[str, Any] = {"tags": node.get("tags", [])}

        if "Paper" in labels:
            node_type = "Paper"
            node_id = node.get("external_id") or node.element_id
            label = node.get("title", node_id)
            metadata.update(
                {
                    "summary": node.get("summary"),
                    "authors": node.get("authors", []),
                    "landing_url": node.get("landing_url"),
                }
            )
            published = Neo4jGraphRepository._coerce_datetime(node.get("published_at"))
            if published:
                metadata["published_at"] = published.isoformat()
        elif "Author" in labels:
            node_type = "Author"
            node_id = node.get("name") or node.element_id
            label = node.get("name", node_id)
            metadata = {}
        elif "Concept" in labels:
            node_type = "Concept"
            node_id = (
                node.get("normalized_name")
                or node.get("name")
                or node.get("external_id")
                or node.element_id
            )
            label = node.get("name", node_id)
            metadata.update({"description": node.get("description")})

        clean_metadata = Neo4jGraphRepository._clean_metadata(metadata)
        return node.element_id, GraphNode(
            id=node_id, label=label, type=node_type, metadata=clean_metadata
        )

    @staticmethod
    def _clean_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value for key, value in metadata.items() if value not in (None, [], {})
        }

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, Neo4jDateTime):
            return value.to_native()
        to_native = getattr(value, "to_native", None)
        if callable(to_native):
            try:
                native = to_native()
                return native if isinstance(native, datetime) else None
            except Exception:  # pragma: no cover - safeguard
                return None
        return None
