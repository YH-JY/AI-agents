from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, ConfigDict

from app.models.domain import AssetNode, AttackEdge


class IngestionMode(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"


class IngestionJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class KubeConfigInfo(BaseModel):
    id: str
    name: str
    clusters: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IngestionJob(BaseModel):
    id: str
    config_id: str
    config_name: str
    mode: IngestionMode
    status: IngestionJobStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    logs: list[str] = Field(default_factory=list)


class IngestionRunRequest(BaseModel):
    config_id: str = Field(alias="configId")
    mode: IngestionMode = IngestionMode.FULL

    model_config = ConfigDict(populate_by_name=True)


class IngestionResult(BaseModel):
    assets: list[AssetNode]
    relationships: list[AttackEdge]


class CypherQueryRequest(BaseModel):
    query: str
    params: dict | None = None


class GraphNode(BaseModel):
    id: str
    labels: list[str] = Field(default_factory=list)
    type: str | None = None
    name: str | None = None
    properties: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "ATTACK_REL"
    properties: dict = Field(default_factory=dict)


class CypherQueryResponse(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    table: list[dict] = Field(default_factory=list)
