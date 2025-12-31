import { create } from "zustand";
import { AttackPath, HealthStatus, NodeType } from "../types";
import { AttackPathFilters } from "../services/api";

interface AttackStoreState {
  filters: AttackPathFilters;
  paths: AttackPath[];
  loading: boolean;
  selectedPathId?: string;
  selectedNodeId?: string;
  health?: HealthStatus;
  setFilters: (filters: AttackPathFilters) => void;
  setPaths: (paths: AttackPath[]) => void;
  setLoading: (loading: boolean) => void;
  selectPath: (pathId?: string) => void;
  selectNode: (nodeId?: string) => void;
  setHealth: (health: HealthStatus) => void;
}

export const useAttackStore = create<AttackStoreState>((set) => ({
  filters: { maxDepth: 6, limit: 5, startType: "Pod" },
  paths: [],
  loading: false,
  selectedPathId: undefined,
  selectedNodeId: undefined,
  health: undefined,
  setFilters: (filters) => set({ filters: { ...filters } }),
  setPaths: (paths) => set({ paths }),
  setLoading: (loading) => set({ loading }),
  selectPath: (selectedPathId) => set({ selectedPathId }),
  selectNode: (selectedNodeId) => set({ selectedNodeId }),
  setHealth: (health) => set({ health })
}));
