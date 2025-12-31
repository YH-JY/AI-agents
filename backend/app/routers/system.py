from fastapi import APIRouter

from app.services.health_service import health_service

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/health")
async def health():
    return health_service.check()
