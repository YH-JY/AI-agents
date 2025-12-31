import axios from "axios";
import {
  AttackPathResponse,
  AssetListResponse,
  HealthStatus,
  NodeType
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000"
});

export interface AttackPathFilters {
  startNodeId?: string;
  startType?: NodeType;
  targetType?: NodeType;
  namespace?: string;
  maxDepth?: number;
  limit?: number;
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
