from __future__ import annotations

from datetime import datetime, timezone

from neo4j.exceptions import Neo4jError

from app.config import get_settings
from app.core.logger import logger
from app.repositories.neo4j_client import neo4j_client


class HealthService:
    def check(self) -> dict[str, str]:
        status = "down"
        version = "unknown"
        try:
            result = neo4j_client.execute("CALL dbms.components() YIELD name, versions")
            if result:
                status = "up"
                version = result[0]["versions"][0]
        except Neo4jError as exc:
            logger.error("Health check failed: %s", exc)
        return {
            "neo4j": status,
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


health_service = HealthService()
