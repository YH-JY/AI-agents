from __future__ import annotations

import re

from fastapi import HTTPException, status

from app.ingestion.models import CypherQueryRequest, CypherQueryResponse
from app.repositories.cypher_repository import cypher_repository


class CypherService:
    FORBIDDEN = re.compile(
        r"\b(CREATE|DELETE|DETACH|DROP|CALL|LOAD|REMOVE|SET|MERGE)\b",
        re.IGNORECASE,
    )

    def execute(self, payload: CypherQueryRequest) -> CypherQueryResponse:
        if not payload.query or not payload.query.strip():
            raise HTTPException(status_code=400, detail="Query is required")
        if self.FORBIDDEN.search(payload.query):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query contains forbidden keywords",
            )
        return cypher_repository.run_query(payload.query, payload.params or {})


cypher_service = CypherService()
