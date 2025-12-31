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

export type QueryMode = "standard" | "shortest" | "highValue";

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

export interface KubeConfigMetadata {
  id: string;
  name: string;
  clusters: string[];
  created_at: string;
}

export type IngestionMode = "full" | "incremental";
export type IngestionJobStatus = "queued" | "running" | "succeeded" | "failed";

export interface IngestionJob {
  id: string;
  config_id: string;
  config_name: string;
  mode: IngestionMode;
  status: IngestionJobStatus;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  logs: string[];
}

export interface GraphNode {
  id: string;
  labels: string[];
  type?: string;
  name?: string;
  properties: Record<string, unknown>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, unknown>;
}

export interface CypherResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  table: Record<string, unknown>[];
}

export interface GraphQueryPayload {
  query: string;
  params?: Record<string, unknown>;
}
