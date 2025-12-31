from fastapi import APIRouter, Depends

from app.dependencies import verify_api_key
from app.ingestion.models import CypherQueryRequest, CypherQueryResponse
from app.services.cypher_service import cypher_service

router = APIRouter(
    prefix="/api/cypher",
    tags=["cypher"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/execute", response_model=CypherQueryResponse)
async def execute_query(payload: CypherQueryRequest):
    return cypher_service.execute(payload)
