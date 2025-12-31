from __future__ import annotations

from app.models.domain import (
    AttackPath,
    AttackPathSearchRequest,
    AttackPathSearchResponse,
    HighValuePathRequest,
    ShortestPathRequest,
)
from app.repositories.attack_path_repository import attack_path_repository


class AttackPathService:
    def search(self, params: AttackPathSearchRequest) -> AttackPathSearchResponse:
        paths: list[AttackPath] = attack_path_repository.search_paths(
            start_node_id=params.start_node_id,
            start_type=params.start_type,
            target_type=params.target_type,
            target_types=None,
            namespace=params.namespace,
            max_depth=params.max_depth,
            limit=params.limit,
        )
        return AttackPathSearchResponse(paths=paths)

    def search_high_value(self, params: HighValuePathRequest) -> AttackPathSearchResponse:
        paths = attack_path_repository.search_high_value_paths(
            start_node_id=params.start_node_id,
            start_type=params.start_type,
            namespace=params.namespace,
            max_depth=params.max_depth,
            limit=params.limit,
            target_types=params.target_types,
        )
        return AttackPathSearchResponse(paths=paths)

    def shortest_path(self, params: ShortestPathRequest) -> AttackPathSearchResponse:
        paths = attack_path_repository.shortest_path(
            start_node_id=params.start_node_id,
            target_node_id=params.target_node_id,
            max_depth=params.max_depth,
        )
        return AttackPathSearchResponse(paths=paths)


attack_path_service = AttackPathService()
