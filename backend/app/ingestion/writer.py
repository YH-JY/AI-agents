from __future__ import annotations

from itertools import islice
from typing import Iterable, List

from app.core.logger import logger
from app.ingestion.models import IngestionMode, IngestionResult
from app.models.domain import AssetNode, AttackEdge
from app.repositories.neo4j_client import neo4j_client


class GraphWriter:
    def write(
        self,
        *,
        result: IngestionResult,
        cluster: str,
        mode: IngestionMode,
    ) -> None:
        logger.info(
            "Writing %s assets and %s relationships for cluster %s",
            len(result.assets),
            len(result.relationships),
            cluster,
        )
        if mode == IngestionMode.FULL:
            neo4j_client.write(
                "MATCH (n:Asset {cluster: $cluster}) DETACH DELETE n",
                {"cluster": cluster},
            )
        self._write_nodes(result.assets)
        self._write_edges(result.relationships)

    def _write_nodes(self, nodes: list[AssetNode]):
        for chunk in _chunk(nodes, 100):
            payload = [self._node_to_payload(node) for node in chunk]
            neo4j_client.write(
                """
                UNWIND $batch AS row
                MERGE (n:Asset {id: row.id})
                SET n += row.props
                """,
                {"batch": payload},
            )

    def _write_edges(self, edges: list[AttackEdge]):
        for chunk in _chunk(edges, 200):
            payload = [self._edge_to_payload(edge) for edge in chunk]
            neo4j_client.write(
                """
                UNWIND $batch AS rel
                MATCH (src:Asset {id: rel.source})
                MATCH (dst:Asset {id: rel.target})
                MERGE (src)-[r:ATTACK_REL {sourceId: rel.source, targetId: rel.target, technique: rel.technique}]->(dst)
                SET r.evidence = rel.evidence,
                    r.confidence = rel.confidence,
                    r.sequence = rel.sequence,
                    r.discoveredAt = rel.discoveredAt
                """,
                {"batch": payload},
            )

    def _node_to_payload(self, node: AssetNode) -> dict:
        props = {
            "id": node.id,
            "name": node.name,
            "namespace": node.namespace,
            "type": node.type.value,
            "criticality": node.criticality,
            "labels": node.labels,
            "lastSeen": node.last_seen.isoformat() if node.last_seen else None,
            "cluster": node.metadata.get("cluster") if node.metadata else None,
        }
        for key, value in (node.metadata or {}).items():
            if value is None:
                continue
            props[f"meta_{key}"] = value
        return {"id": node.id, "props": props}

    def _edge_to_payload(self, edge: AttackEdge) -> dict:
        return {
            "source": edge.source,
            "target": edge.target,
            "technique": str(edge.technique),
            "evidence": edge.evidence,
            "confidence": edge.confidence,
            "sequence": edge.sequence,
            "discoveredAt": None,
        }


def _chunk(iterable: Iterable, size: int):
    iterator = iter(iterable)
    while True:
        batch = list(islice(iterator, size))
        if not batch:
            break
        yield batch
