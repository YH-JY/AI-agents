from __future__ import annotations

from app.models.domain import (
    AttackPath,
    AttackPathSearchRequest,
    AttackPathSearchResponse,
)
from app.repositories.attack_path_repository import attack_path_repository


class AttackPathService:
    def search(self, params: AttackPathSearchRequest) -> AttackPathSearchResponse:
        paths: list[AttackPath] = attack_path_repository.search_paths(
            start_node_id=params.start_node_id,
            start_type=params.start_type,
            target_type=params.target_type,
            namespace=params.namespace,
            max_depth=params.max_depth,
            limit=params.limit,
        )
        return AttackPathSearchResponse(paths=paths)


attack_path_service = AttackPathService()
