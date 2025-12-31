from __future__ import annotations

from app.models.domain import (
    AssetDetailResponse,
    AssetFilter,
    AssetListResponse,
)
from app.repositories.asset_repository import asset_repository


class AssetService:
    def list_assets(self, filters: AssetFilter) -> AssetListResponse:
        items, total = asset_repository.list_assets(filters)
        return AssetListResponse(
            items=items, total=total, page=filters.page, page_size=filters.page_size
        )

    def get_asset(self, asset_id: str) -> AssetDetailResponse | None:
        return asset_repository.get_asset_detail(asset_id)


asset_service = AssetService()
