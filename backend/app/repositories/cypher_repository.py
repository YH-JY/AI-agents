from __future__ import annotations

from typing import Any, List

from neo4j.graph import Node, Relationship, Path

from app.ingestion.models import CypherQueryResponse, GraphEdge, GraphNode
from app.repositories.neo4j_client import neo4j_client


class CypherRepository:
    def run_query(self, query: str, params: dict | None = None) -> CypherQueryResponse:
        records = neo4j_client.query(query, params or {})
        node_map: dict[str, GraphNode] = {}
        edge_map: dict[str, GraphEdge] = {}
        table: list[dict[str, Any]] = []

        for record in records:
            row = {}
            for key, value in record.items():
                converted = self._convert_value(value, node_map, edge_map)
                row[key] = converted
            table.append(row)

        return CypherQueryResponse(
            nodes=list(node_map.values()),
            edges=list(edge_map.values()),
            table=table,
        )

    def _convert_value(
        self,
        value,
        node_map: dict[str, GraphNode],
        edge_map: dict[str, GraphEdge],
    ):
        if isinstance(value, Node):
            node = self._node_from(value)
            node_map[node.id] = node
            return {"node": node.id}
        if isinstance(value, Relationship):
            edge = self._edge_from(value)
            edge_map[edge.id] = edge
            return {"edge": edge.id}
        if isinstance(value, Path):
            for node in value.nodes:
                graph_node = self._node_from(node)
                node_map[graph_node.id] = graph_node
            for rel in value.relationships:
                graph_edge = self._edge_from(rel)
                edge_map[graph_edge.id] = graph_edge
            return {"path": [n["id"] for n in value.nodes]}
        if isinstance(value, list):
            return [
                self._convert_value(item, node_map, edge_map) for item in value
            ]
        return value

    def _node_from(self, node: Node) -> GraphNode:
        properties = dict(node)
        node_id = properties.get("id") or node.element_id
        return GraphNode(
            id=node_id,
            labels=list(node.labels),
            type=properties.get("type"),
            name=properties.get("name"),
            properties=properties,
        )

    def _edge_from(self, rel: Relationship) -> GraphEdge:
        properties = dict(rel)
        rel_id = properties.get("id") or rel.element_id
        source = rel.start_node["id"] if "id" in rel.start_node else rel.start_node.element_id
        target = rel.end_node["id"] if "id" in rel.end_node else rel.end_node.element_id
        return GraphEdge(
            id=str(rel_id),
            source=source,
            target=target,
            type=rel.type,
            properties=properties,
        )


cypher_repository = CypherRepository()
