from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Dict, List

import yaml
from fastapi import UploadFile

from app.core.logger import logger
from app.ingestion.models import (
    IngestionJob,
    IngestionJobStatus,
    IngestionMode,
    KubeConfigInfo,
)


class KubeconfigRegistry:
    def __init__(self, kubeconfig_dir: Path):
        self.kubeconfig_dir = kubeconfig_dir
        self.kubeconfig_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile) -> KubeConfigInfo:
        config_id = str(uuid.uuid4())
        dest = self.kubeconfig_dir / f"{config_id}.yaml"
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        metadata = self._extract_metadata(dest, config_id)
        self._write_metadata(metadata)
        logger.info("Stored kubeconfig %s", config_id)
        return metadata

    def list(self) -> list[KubeConfigInfo]:
        configs: list[KubeConfigInfo] = []
        for meta_file in self.kubeconfig_dir.glob("*.meta.json"):
            try:
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                configs.append(KubeConfigInfo(**data))
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to load kubeconfig metadata %s: %s", meta_file, exc)
        return sorted(configs, key=lambda item: item.created_at, reverse=True)

    def get(self, config_id: str) -> KubeConfigInfo:
        meta_path = self._meta_path(config_id)
        if not meta_path.exists():
            raise FileNotFoundError(f"Config {config_id} not found")
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return KubeConfigInfo(**data)

    def path_for(self, config_id: str) -> Path:
        file_path = self.kubeconfig_dir / f"{config_id}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Kubeconfig {config_id} not found")
        return file_path

    def _extract_metadata(self, path: Path, config_id: str) -> KubeConfigInfo:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        clusters = [cluster["name"] for cluster in data.get("clusters", [])]
        name = data.get("current-context") or (clusters[0] if clusters else config_id)
        return KubeConfigInfo(
            id=config_id,
            name=name,
            clusters=clusters or [name],
            created_at=datetime.utcnow(),
        )

    def _write_metadata(self, metadata: KubeConfigInfo) -> None:
        meta_path = self._meta_path(metadata.id)
        meta_path.write_text(metadata.model_dump_json(), encoding="utf-8")

    def _meta_path(self, config_id: str) -> Path:
        return self.kubeconfig_dir / f"{config_id}.meta.json"


class IngestionJobStore:
    def __init__(self, retention_hours: int = 24):
        self._jobs: Dict[str, dict] = {}
        self._lock = Lock()
        self._retention = timedelta(hours=retention_hours)

    def create(self, config: KubeConfigInfo, mode: IngestionMode) -> IngestionJob:
        job_id = str(uuid.uuid4())
        job = {
            "id": job_id,
            "config_id": config.id,
            "config_name": config.name,
            "mode": mode,
            "status": IngestionJobStatus.QUEUED,
            "created_at": datetime.utcnow(),
            "started_at": None,
            "finished_at": None,
            "logs": [],
        }
        with self._lock:
            self._jobs[job_id] = job
            self._evict()
        return IngestionJob(**job)

    def update_status(
        self,
        job_id: str,
        *,
        status: IngestionJobStatus,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ):
        with self._lock:
            job = self._require(job_id)
            job["status"] = status
            if started_at:
                job["started_at"] = started_at
            if finished_at:
                job["finished_at"] = finished_at

    def append_log(self, job_id: str, message: str):
        with self._lock:
            job = self._require(job_id)
            job["logs"].append(f"{datetime.utcnow().isoformat()} {message}")

    def get(self, job_id: str) -> IngestionJob:
        with self._lock:
            job = self._require(job_id)
            return IngestionJob(**job)

    def list(self) -> list[IngestionJob]:
        with self._lock:
            self._evict()
            return [IngestionJob(**job) for job in self._jobs.values()]

    def _require(self, job_id: str) -> dict:
        if job_id not in self._jobs:
            raise KeyError(f"Job {job_id} not found")
        return self._jobs[job_id]

    def _evict(self):
        threshold = datetime.utcnow() - self._retention
        to_delete = [
            job_id
            for job_id, job in self._jobs.items()
            if job["finished_at"] and job["finished_at"] < threshold
        ]
        for job_id in to_delete:
            self._jobs.pop(job_id, None)
