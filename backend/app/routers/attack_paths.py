from fastapi import APIRouter, Depends

from app.dependencies import verify_api_key
from app.models.domain import AttackPathSearchRequest, AttackPathSearchResponse
from app.services.attack_path_service import attack_path_service

router = APIRouter(
    prefix="/api/attack-paths",
    tags=["attack-paths"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/search", response_model=AttackPathSearchResponse)
async def search_attack_paths(payload: AttackPathSearchRequest):
    return attack_path_service.search(payload)
