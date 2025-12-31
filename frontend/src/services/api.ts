import axios from "axios";
import {
  AttackPathResponse,
  AssetListResponse,
  CypherResult,
  GraphQueryPayload,
  HealthStatus,
  IngestionJob,
  IngestionMode,
  KubeConfigMetadata,
  NodeType
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000"
});

export interface AttackPathFilters {
  startNodeId?: string;
  startType?: NodeType;
  targetType?: NodeType;
  targetNodeId?: string;
  queryMode?: "standard" | "shortest" | "highValue";
  namespace?: string;
  maxDepth?: number;
  limit?: number;
  targetTypes?: NodeType[];
}

export const searchAttackPaths = async (
  filters: AttackPathFilters
): Promise<AttackPathResponse> => {
  const { data } = await api.post<AttackPathResponse>(
    "/api/attack-paths/search",
    filters
  );
  return data;
};

export const searchShortestPath = async (
  payload: Pick<AttackPathFilters, "startNodeId" | "targetNodeId" | "maxDepth">
): Promise<AttackPathResponse> => {
  const { data } = await api.post<AttackPathResponse>(
    "/api/attack-paths/shortest",
    payload
  );
  return data;
};

export const searchHighValuePaths = async (
  payload: Pick<
    AttackPathFilters,
    "startNodeId" | "startType" | "namespace" | "maxDepth" | "limit" | "targetTypes"
  >
): Promise<AttackPathResponse> => {
  const { data } = await api.post<AttackPathResponse>(
    "/api/attack-paths/high-value",
    payload
  );
  return data;
};

export const fetchAssets = async (params: {
  type?: NodeType;
  namespace?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}): Promise<AssetListResponse> => {
  const { data } = await api.get<AssetListResponse>("/api/assets", {
    params
  });
  return data;
};

export const fetchHealth = async (): Promise<HealthStatus> => {
  const { data } = await api.get<HealthStatus>("/api/system/health");
  return data;
};

export const uploadKubeconfig = async (file: File): Promise<KubeConfigMetadata> => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<KubeConfigMetadata>(
    "/api/ingestion/kubeconfig",
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" }
    }
  );
  return data;
};

export const listKubeconfigs = async (): Promise<KubeConfigMetadata[]> => {
  const { data } = await api.get<KubeConfigMetadata[]>("/api/ingestion/configs");
  return data;
};

export const runIngestion = async (params: {
  configId: string;
  mode: IngestionMode;
}) => {
  const { data } = await api.post("/api/ingestion/run", {
    configId: params.configId,
    mode: params.mode
  });
  return data as IngestionJob;
};

export const listIngestionJobs = async (): Promise<IngestionJob[]> => {
  const { data } = await api.get<IngestionJob[]>("/api/ingestion/jobs");
  return data;
};

export const executeCypher = async (
  params: GraphQueryPayload
): Promise<CypherResult> => {
  const { data } = await api.post<CypherResult>("/api/cypher/execute", params);
  return data;
};
