export type NodeType =
  | "Container"
  | "Pod"
  | "Volume"
  | "Node"
  | "ServiceAccount"
  | "Secret"
  | "Credential"
  | "Master";

export interface AssetNode {
  id: string;
  type: NodeType;
  name: string;
  namespace?: string;
  criticality: string;
  labels?: string[];
  metadata?: Record<string, unknown>;
}

export interface AttackEdge {
  source: string;
  target: string;
  technique: string;
  evidence?: string;
  confidence?: number;
  sequence?: number;
}

export interface AttackStep {
  depth: number;
  nodes: AssetNode[];
  edges: AttackEdge[];
}

export interface AttackPath {
  id: string;
  score: number;
  steps: AttackStep[];
  summary: string;
}

export interface AttackPathResponse {
  paths: AttackPath[];
}

export interface HealthStatus {
  neo4j: "up" | "down";
  version: string;
  timestamp: string;
}

export interface AssetSummary {
  id: string;
  type: NodeType;
  name: string;
  namespace?: string;
  criticality: string;
}

export interface AssetListResponse {
  items: AssetSummary[];
  total: number;
  page: number;
  pageSize: number;
}
