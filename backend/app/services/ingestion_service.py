from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, HTTPException, UploadFile, status

from app.config import get_settings
from app.core.logger import logger
from app.ingestion.collectors import KubernetesCollector
from app.ingestion.manager import IngestionJobStore, KubeconfigRegistry
from app.ingestion.models import (
    IngestionJob,
    IngestionJobStatus,
    IngestionMode,
    KubeConfigInfo,
)
from app.ingestion.writer import GraphWriter


class IngestionService:
    def __init__(self):
        settings = get_settings()
        self.registry = KubeconfigRegistry(Path(settings.kubeconfig_dir))
        self.job_store = IngestionJobStore(settings.ingestion_job_retention_hours)
        self.graph_writer = GraphWriter()

    def upload_kubeconfig(self, file: UploadFile) -> KubeConfigInfo:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing filename")
        if not file.filename.endswith((".yaml", ".yml", ".conf")):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        return self.registry.save(file)

    def list_kubeconfigs(self) -> list[KubeConfigInfo]:
        return self.registry.list()

    def start_job(
        self,
        *,
        background_tasks: BackgroundTasks,
        config_id: str,
        mode: IngestionMode,
    ) -> IngestionJob:
        try:
            config = self.registry.get(config_id)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        job = self.job_store.create(config, mode)
        background_tasks.add_task(self._run_job, job.id, config, mode)
        return job

    def list_jobs(self) -> list[IngestionJob]:
        return self.job_store.list()

    def get_job(self, job_id: str) -> IngestionJob:
        try:
            return self.job_store.get(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    def _run_job(self, job_id: str, config: KubeConfigInfo, mode: IngestionMode):
        logger.info("Starting ingestion job %s for config %s", job_id, config.id)
        self.job_store.update_status(
            job_id,
            status=IngestionJobStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        self.job_store.append_log(job_id, "Connecting to cluster")
        kubeconfig_path = self.registry.path_for(config.id)
        collector = KubernetesCollector(kubeconfig_path, cluster_name=config.name)
        try:
            result = collector.collect()
            self.job_store.append_log(job_id, f"Collected {len(result.assets)} assets")
            self.graph_writer.write(result=result, cluster=config.name, mode=mode)
            self.job_store.append_log(job_id, "Graph write completed")
            self.job_store.update_status(
                job_id,
                status=IngestionJobStatus.SUCCEEDED,
                finished_at=datetime.utcnow(),
            )
            logger.info("Ingestion job %s succeeded", job_id)
        except Exception as exc:  # pragma: no cover
            logger.exception("Ingestion job %s failed", job_id)
            self.job_store.append_log(job_id, f"Failed: {exc}")
            self.job_store.update_status(
                job_id,
                status=IngestionJobStatus.FAILED,
                finished_at=datetime.utcnow(),
            )


ingestion_service = IngestionService()
