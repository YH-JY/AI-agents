from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class NodeType(str, Enum):
    CONTAINER = "Container"
    POD = "Pod"
    VOLUME = "Volume"
    NODE = "Node"
    SERVICE_ACCOUNT = "ServiceAccount"
    SECRET = "Secret"
    CREDENTIAL = "Credential"
    MASTER = "Master"


class AttackTechnique(str, Enum):
    BELONGS_TO = "属于"
    MOUNT_DISCOVERY = "挂载发现"
    ROOT_ACCESS = "根目录"
    LATERAL_MOVEMENT = "横向移动"
    PRIV_DISCOVERY = "权限发现"
    RBAC_ABUSE = "RBAC权限利用"
    CLUSTER_CREDS = "集群凭证获取"
    TAINT_LATERAL = "污点横向"


class AssetNode(BaseModel):
    id: str
    type: NodeType
    name: str
    namespace: str | None = None
    criticality: str = "MEDIUM"
    labels: list[str] = Field(default_factory=list)
    last_seen: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AttackEdge(BaseModel):
    source: str
    target: str
    technique: AttackTechnique | str
    evidence: str | None = None
    confidence: float | None = None
    sequence: int | None = None


class AttackStep(BaseModel):
    depth: int
    nodes: list[AssetNode]
    edges: list[AttackEdge]


class AttackPath(BaseModel):
    id: str
    score: float
    steps: list[AttackStep]
    summary: str


class AttackPathSearchRequest(BaseModel):
    start_node_id: str | None = Field(None, alias="startNodeId")
    start_type: NodeType | None = Field(None, alias="startType")
    target_type: NodeType | None = Field(None, alias="targetType")
    namespace: str | None = None
    max_depth: int = Field(6, alias="maxDepth", ge=1, le=8)
    limit: int = Field(5, ge=1, le=20)

    @root_validator
    def ensure_start(cls, values):
        if not values.get("start_node_id") and not values.get("start_type"):
            raise ValueError("startNodeId or startType is required")
        return values

    class Config:
        allow_population_by_field_name = True


class AttackPathSearchResponse(BaseModel):
    paths: list[AttackPath]


class AssetFilter(BaseModel):
    type: NodeType | None = None
    namespace: str | None = None
    search: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(25, alias="pageSize", ge=1, le=100)

    class Config:
        allow_population_by_field_name = True


class AssetSummary(BaseModel):
    id: str
    type: NodeType
    name: str
    namespace: str | None = None
    criticality: str
    labels: list[str] = Field(default_factory=list)


class AssetListResponse(BaseModel):
    items: list[AssetSummary]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    class Config:
        allow_population_by_field_name = True


class AssetDetailResponse(BaseModel):
    node: AssetNode
    inbound_edges: list[AttackEdge]
    outbound_edges: list[AttackEdge]
