"""Neo4j repository utilities."""

from __future__ import annotations

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
    def from_settings(cls, uri: str, user: str, password: str) -> "Neo4jGraphRepository":
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
            return await session.execute_read(self._paper_exists_tx, external_id=external_id)

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
            return await session.execute_read(self._get_paper_tx, external_id=external_id)

    async def get_paper_graph(self, external_id: str) -> PaperGraph:
        async with self._driver.session() as session:
            return await session.execute_read(self._get_paper_graph_tx, external_id=external_id)

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
                    published_at=Neo4jGraphRepository._coerce_datetime(node.get("published_at")),
                    storage_path=Path(node.get("storage_path")) if node.get("storage_path") else None,
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
            published_at=Neo4jGraphRepository._coerce_datetime(node.get("published_at")),
            storage_path=Path(node.get("storage_path")) if node.get("storage_path") else None,
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

        nodes = [
            GraphNode(
                id=paper_node["external_id"],
                label=paper_node.get("title", "Paper"),
                type="Paper",
                metadata={
                    "summary": paper_node.get("summary"),
                    "tags": paper_node.get("tags", []),
                },
            )
        ]
        for node in related_nodes:
            label = node.get("name") or node.get("title") or node.element_id
            node_type = next(iter(node.labels), "Entity")
            nodes.append(
                GraphNode(
                    id=node["external_id"] if "external_id" in node else node.element_id,
                    label=label,
                    type=node_type,
                    metadata={"tags": node.get("tags", [])},
                )
            )

        edges: list[GraphEdge] = []
        for rel in relationships:
            edges.append(
                GraphEdge(
                    id=rel.element_id,
                    source=rel.start_node["external_id"],
                    target=rel.end_node.get("external_id")
                    or rel.end_node.get("name")
                    or rel.end_node.element_id,
                    type=rel.type,
                    metadata=dict(rel),
                )
            )
        return PaperGraph(nodes=nodes, edges=edges)

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
        node_map: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        async for record in result:
            paper = record["p"]
            other = record["other"]
            concept = record["c"]
            rel = record["r"]
            rel_other = record["r2"]
            for node, label, node_type in (
                (paper, paper.get("title", "Paper"), "Paper"),
                (other, other.get("title", "Paper"), "Paper"),
                (concept, concept.get("name", "Concept"), "Concept"),
            ):
                node_id = node.get("external_id") or node.get("name") or node.element_id
                if node_id not in node_map:
                        metadata = {"tags": node.get("tags", [])}
                        if node_type == "Paper":
                            metadata["summary"] = node.get("summary")
                            published = Neo4jGraphRepository._coerce_datetime(node.get("published_at"))
                            metadata["published_at"] = published.isoformat() if published else None
                        node_map[node_id] = GraphNode(
                            id=node_id,
                            label=label,
                            type=node_type,
                            metadata=metadata,
                    )
            edges.append(
                GraphEdge(
                    id=rel.element_id,
                    source=paper.get("external_id"),
                    target=concept.get("name") or concept.element_id,
                    type="RELATES_TO",
                    metadata={"relation": rel.get("relation")},
                )
            )
            edges.append(
                GraphEdge(
                    id=f"{rel.element_id}-other",
                    source=other.get("external_id"),
                    target=concept.get("name") or concept.element_id,
                    type="RELATES_TO",
                    metadata={"relation": rel_other.get("relation") if rel_other else "RELATES_TO"},
                )
            )
        return PaperGraph(nodes=list(node_map.values()), edges=edges)

    @staticmethod
    async def _upsert_paper_tx(tx, *, record: dict, analysis: dict, storage_path: str) -> None:
        await (await tx.run(
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
        )).consume()

    @staticmethod
    def _normalize_concept_name(name: str) -> str:
        slug = _NORMALIZE_PATTERN.sub("-", name.lower()).strip("-")
        return slug or name.lower()

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
