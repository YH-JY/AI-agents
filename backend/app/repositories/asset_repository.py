from __future__ import annotations

from app.core.logger import logger
from app.models.domain import (
    AssetDetailResponse,
    AssetFilter,
    AssetNode,
    AssetStats,
    AssetSummary,
    AttackEdge,
    NodeType,
)
from app.repositories.neo4j_client import neo4j_client


class AssetRepository:
    def list_assets(self, filters: AssetFilter) -> tuple[list[AssetSummary], int]:
        where_clauses = []
        params: dict[str, str | int] = {
            "skip": (filters.page - 1) * filters.page_size,
            "limit": filters.page_size,
        }
        if filters.type:
            where_clauses.append("n.type = $type")
            params["type"] = filters.type.value
        if filters.namespace:
            where_clauses.append("coalesce(n.namespace,'') CONTAINS $namespace")
            params["namespace"] = filters.namespace
        if filters.search:
            where_clauses.append(
                "(toLower(n.name) CONTAINS toLower($search) OR n.id = $search)"
            )
            params["search"] = filters.search
        where = ""
        if where_clauses:
            where = "WHERE " + " AND ".join(where_clauses)

        list_query = f"""
        MATCH (n:Asset)
        {where}
        RETURN n
        ORDER BY coalesce(n.lastSeen, datetime()) DESC
        SKIP $skip
        LIMIT $limit
        """
        count_query = f"""
        MATCH (n:Asset)
        {where}
        RETURN count(n) AS total
        """
        result = neo4j_client.execute(list_query, params)
        count_result = neo4j_client.execute(count_query, params)
        total = count_result[0]["total"] if count_result else 0
        summaries = [
            AssetSummary(
                id=record["n"]["id"],
                type=NodeType(record["n"]["type"]),
                name=record["n"]["name"],
                namespace=record["n"].get("namespace"),
                criticality=record["n"].get("criticality", "MEDIUM"),
                labels=record["n"].get("labels", []),
            )
            for record in result
        ]
        return summaries, total

    def get_asset_detail(self, asset_id: str) -> AssetDetailResponse | None:
        query = """
        MATCH (n:Asset {id: $assetId})
        OPTIONAL MATCH (src:Asset)-[inRel:ATTACK_REL]->(n)
        OPTIONAL MATCH (n)-[outRel:ATTACK_REL]->(dst:Asset)
        RETURN n,
               collect(DISTINCT {
                 source: src.id,
                 target: n.id,
                 technique: inRel.technique,
                 evidence: inRel.evidence,
                 confidence: inRel.confidence,
                 sequence: inRel.sequence
               }) AS inbound,
               collect(DISTINCT {
                 source: n.id,
                 target: dst.id,
                 technique: outRel.technique,
                 evidence: outRel.evidence,
                 confidence: outRel.confidence,
                 sequence: outRel.sequence
               }) AS outbound
        """
        records = neo4j_client.execute(query, {"assetId": asset_id})
        if not records:
            return None
        record = records[0]
        node = self._node_from(record["n"])
        inbound_edges = [
            AttackEdge(
                source=entry["source"],
                target=entry["target"],
                technique=entry["technique"],
                evidence=entry["evidence"],
                confidence=entry["confidence"],
                sequence=entry["sequence"],
            )
            for entry in record["inbound"]
            if entry["source"] and entry["target"]
        ]
        outbound_edges = [
            AttackEdge(
                source=entry["source"],
                target=entry["target"],
                technique=entry["technique"],
                evidence=entry["evidence"],
                confidence=entry["confidence"],
                sequence=entry["sequence"],
            )
            for entry in record["outbound"]
            if entry["source"] and entry["target"]
        ]
        return AssetDetailResponse(
            node=node,
            inbound_edges=inbound_edges,
            outbound_edges=outbound_edges,
        )

    def get_asset_stats(self) -> list[AssetStats]:
        query = """
        MATCH (n:Asset)
        RETURN n.type AS type, count(n) AS total
        """
        records = neo4j_client.execute(query, {})
        stats: list[AssetStats] = []
        for record in records:
            node_type = record.get("type")
            total = record.get("total")
            if not node_type or total is None:
                continue
            try:
                stats.append(AssetStats(type=NodeType(node_type), total=total))
            except ValueError:
                logger.warning("Unknown node type in stats: %s", node_type)
        return stats

    def _node_from(self, node) -> AssetNode:
        metadata = dict(node)
        for key in ["type", "id", "name", "namespace", "criticality", "labels", "lastSeen"]:
            metadata.pop(key, None)
        return AssetNode(
            id=node["id"],
            type=NodeType(node["type"]),
            name=node["name"],
            namespace=node.get("namespace"),
            criticality=node.get("criticality", "MEDIUM"),
            labels=node.get("labels", []),
            metadata=metadata,
        )

asset_repository = AssetRepository()
