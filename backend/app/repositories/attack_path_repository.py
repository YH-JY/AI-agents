from __future__ import annotations

import uuid
from typing import Any, List

from neo4j.graph import Path

from app.models.domain import (
    AssetNode,
    AttackEdge,
    AttackPath,
    AttackStep,
    AttackTechnique,
    NodeType,
)
from app.repositories.neo4j_client import neo4j_client


class AttackPathRepository:
    def search_paths(
        self,
        *,
        start_node_id: str | None,
        start_type: NodeType | None,
        target_type: NodeType | None,
        namespace: str | None,
        max_depth: int,
        limit: int,
    ) -> list[AttackPath]:
        filters = []
        params: dict[str, Any] = {
            "maxDepth": max_depth,
            "limit": limit,
        }
        if start_node_id:
            filters.append("start.id = $startNodeId")
            params["startNodeId"] = start_node_id
        if start_type:
            filters.append("start.type = $startType")
            params["startType"] = start_type.value
        if namespace:
            filters.append("coalesce(start.namespace,'') = $namespace")
            params["namespace"] = namespace

        where_clause = ""
        if filters:
            where_clause = "WHERE " + " AND ".join(filters)

        target_filters = []
        if target_type:
            target_filters.append("target.type = $targetType")
            params["targetType"] = target_type.value
        if namespace:
            target_filters.append("coalesce(target.namespace,'') = $namespace")

        target_where = ""
        if target_filters:
            target_where = "WHERE " + " AND ".join(target_filters)

        query = f"""
        MATCH (start:Asset)
        {where_clause}
        MATCH path = (start)-[rels:ATTACK_REL*1..$maxDepth]->(target:Asset)
        {target_where}
        WITH path,
        reduce(score = 0.0, rel IN relationships(path) |
            score + coalesce(rel.confidence, 0.2) +
            CASE endNode(rel).criticality
                WHEN 'HIGH' THEN 2.0
                WHEN 'MEDIUM' THEN 1.0
                ELSE 0.5
            END
        ) AS score
        RETURN path, score
        ORDER BY score DESC
        LIMIT $limit
        """
        records = neo4j_client.execute(query, params)
        return [self._map_record(record) for record in records]

    def _map_record(self, record: dict[str, Any]) -> AttackPath:
        path: Path = record["path"]
        score: float = record.get("score", 0.0)
        nodes = list(path.nodes)
        relationships = list(path.relationships)

        attack_steps: list[AttackStep] = []
        if nodes:
            attack_steps.append(
                AttackStep(
                    depth=0,
                    nodes=[self._node_from_neo4j(nodes[0])],
                    edges=[],
                )
            )
        for idx, rel in enumerate(relationships, start=1):
            attack_steps.append(
                AttackStep(
                    depth=idx,
                    nodes=[self._node_from_neo4j(rel.end_node)],
                    edges=[self._edge_from_rel(rel)],
                )
            )

        summary = ""
        if nodes:
            summary = f"{nodes[0]['name']} → {nodes[-1]['name']} ({len(relationships)} hops)"

        return AttackPath(
            id=str(uuid.uuid4()),
            score=round(score, 2),
            steps=attack_steps,
            summary=summary,
        )

    def _node_from_neo4j(self, node) -> AssetNode:
        node_type = NodeType(node["type"])
        metadata = dict(node)
        metadata.pop("type", None)
        metadata.pop("id", None)
        metadata.pop("name", None)
        metadata.pop("namespace", None)
        metadata.pop("criticality", None)
        metadata.pop("labels", None)
        metadata.pop("lastSeen", None)

        return AssetNode(
            id=node["id"],
            type=node_type,
            name=node.get("name"),
            namespace=node.get("namespace"),
            criticality=node.get("criticality", "MEDIUM"),
            labels=node.get("labels", []),
            metadata=metadata,
        )

    def _edge_from_rel(self, rel) -> AttackEdge:
        technique_value = rel.get("technique")
        try:
            technique = AttackTechnique(technique_value)
        except ValueError:
            technique = technique_value

        return AttackEdge(
            source=rel.start_node["id"],
            target=rel.end_node["id"],
            technique=technique,
            evidence=rel.get("evidence"),
            confidence=rel.get("confidence"),
            sequence=rel.get("sequence"),
        )


attack_path_repository = AttackPathRepository()
