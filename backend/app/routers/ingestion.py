from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile

from app.dependencies import verify_api_key
from app.ingestion.models import IngestionJob, IngestionRunRequest, KubeConfigInfo
from app.services.ingestion_service import ingestion_service

router = APIRouter(
    prefix="/api/ingestion",
    tags=["ingestion"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/kubeconfig", response_model=KubeConfigInfo)
async def upload_kubeconfig(file: UploadFile):
    return ingestion_service.upload_kubeconfig(file)


@router.get("/configs", response_model=list[KubeConfigInfo])
async def list_configs():
    return ingestion_service.list_kubeconfigs()


@router.post("/run")
async def run_ingestion(request: IngestionRunRequest, background_tasks: BackgroundTasks):
    job = ingestion_service.start_job(
        background_tasks=background_tasks,
        config_id=request.config_id,
        mode=request.mode,
    )
    return job


@router.get("/jobs", response_model=list[IngestionJob])
async def list_jobs():
    return ingestion_service.list_jobs()


@router.get("/jobs/{job_id}", response_model=IngestionJob)
async def get_job(job_id: str):
    return ingestion_service.get_job(job_id)
