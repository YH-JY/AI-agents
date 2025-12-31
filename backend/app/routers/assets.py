from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import verify_api_key
from app.models.domain import (
    AssetDetailResponse,
    AssetFilter,
    AssetListResponse,
    AssetStatsResponse,
    NodeType,
)
from app.services.asset_service import asset_service

router = APIRouter(
    prefix="/api/assets",
    tags=["assets"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("", response_model=AssetListResponse)
async def list_assets(
    type: NodeType | None = Query(default=None),
    namespace: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100, alias="pageSize"),
):
    filters = AssetFilter(
        type=type,
        namespace=namespace,
        search=search,
        page=page,
        page_size=page_size,
    )
    return asset_service.list_assets(filters)


@router.get("/stats/summary", response_model=AssetStatsResponse)
async def asset_stats():
    return asset_service.get_stats()


@router.get("/{asset_id}", response_model=AssetDetailResponse)
async def get_asset(asset_id: str):
    asset = asset_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset
