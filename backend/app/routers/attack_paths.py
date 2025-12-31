from fastapi import APIRouter, Depends

from app.dependencies import verify_api_key
from app.models.domain import (
    AttackPathSearchRequest,
    AttackPathSearchResponse,
    HighValuePathRequest,
    ShortestPathRequest,
)
from app.services.attack_path_service import attack_path_service

router = APIRouter(
    prefix="/api/attack-paths",
    tags=["attack-paths"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/search", response_model=AttackPathSearchResponse)
async def search_attack_paths(payload: AttackPathSearchRequest):
    return attack_path_service.search(payload)


@router.post("/high-value", response_model=AttackPathSearchResponse)
async def search_high_value_paths(payload: HighValuePathRequest):
    return attack_path_service.search_high_value(payload)


@router.post("/shortest", response_model=AttackPathSearchResponse)
async def shortest_path(payload: ShortestPathRequest):
    return attack_path_service.shortest_path(payload)
