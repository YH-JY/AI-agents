from __future__ import annotations

from typing import Any, Callable

from neo4j import GraphDatabase, Session, basic_auth

from app.config import get_settings
from app.core.logger import logger


class Neo4jClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=basic_auth(settings.neo4j_user, settings.neo4j_password),
        )
        self._database = settings.neo4j_database

    def close(self) -> None:
        self._driver.close()

    def execute(self, query: str, parameters: dict[str, Any] | None = None):
        settings = get_settings()
        parameters = parameters or {}
        logger.debug("Running Cypher %s with %s", query, parameters)
        with self._driver.session(database=self._database) as session:
            return session.read_transaction(
                lambda tx: tx.run(query, parameters).data()
            )

    def write(self, query: str, parameters: dict[str, Any] | None = None):
        parameters = parameters or {}
        with self._driver.session(database=self._database) as session:
            return session.write_transaction(
                lambda tx: tx.run(query, parameters).data()
            )


neo4j_client = Neo4jClient()
