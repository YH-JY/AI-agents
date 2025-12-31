import { useEffect } from "react";
import { Card, Empty, Spin, Tabs, Typography, message } from "antd";
import { FilterPanel } from "./components/FilterPanel";
import { AttackGraph } from "./components/AttackGraph";
import { AssetList } from "./components/AssetList";
import { HealthIndicator } from "./components/HealthIndicator";
import { PathSummaryDrawer } from "./components/PathSummaryDrawer";
import { IngestionPanel } from "./components/IngestionPanel";
import { CypherConsole } from "./components/CypherConsole";
import { useAttackStore } from "./store/useAttackStore";
import {
  fetchHealth,
  searchAttackPaths,
  searchHighValuePaths,
  searchShortestPath
} from "./services/api";

const App = () => {
  const {
    filters,
    paths,
    loading,
    selectedPathId,
    setFilters,
    setPaths,
    setLoading,
    selectPath,
    selectNode,
    health,
    setHealth
  } = useAttackStore();

  const handleSearch = async (nextFilters = filters) => {
    if (
      nextFilters.queryMode === "shortest" &&
      (!nextFilters.startNodeId || !nextFilters.targetNodeId)
    ) {
      message.warning("最短路径需要同时指定起点和终点 ID");
      return;
    }
    setFilters(nextFilters);
    setLoading(true);
    try {
      let result;
      if (nextFilters.queryMode === "highValue") {
        result = await searchHighValuePaths({
          startNodeId: nextFilters.startNodeId,
          startType: nextFilters.startType,
          namespace: nextFilters.namespace,
          limit: nextFilters.limit,
          maxDepth: nextFilters.maxDepth,
          targetTypes: nextFilters.targetTypes?.length
            ? nextFilters.targetTypes
            : ["Master", "Credential"]
        });
      } else if (nextFilters.queryMode === "shortest") {
        result = await searchShortestPath({
          startNodeId: nextFilters.startNodeId,
          targetNodeId: nextFilters.targetNodeId,
          maxDepth: nextFilters.maxDepth
        });
      } else {
        result = await searchAttackPaths(nextFilters);
      }
      setPaths(result.paths);
      selectPath(result.paths[0]?.id);
    } finally {
      setLoading(false);
    }
  };

  const handleAssetSelect = (assetId: string) => {
    const nextFilters = { ...filters, startNodeId: assetId };
    handleSearch(nextFilters);
  };

  const refreshHealth = async () => {
    const result = await fetchHealth();
    setHealth(result);
  };

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const selectedPath = paths.find((path) => path.id === selectedPathId);

  const pathTab = (
    <div className="path-layout">
      <FilterPanel onSearch={handleSearch} />
      <div className="graph-container">
        <div className="panel-header">
          <Typography.Text style={{ color: "#94a3b8" }}>
            根据过滤条件自动计算或筛选攻击路径
          </Typography.Text>
        </div>
        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ flex: 1 }}>
            {loading ? (
              <Spin tip="计算路径..." />
            ) : paths.length === 0 ? (
              <Empty description="暂无路径结果" />
            ) : (
              <>
                <div className="path-cards">
                  {paths.map((path) => (
                    <Card
                      key={path.id}
                      className={
                        path.id === selectedPathId ? "path-card selected" : "path-card"
                      }
                      onClick={() => selectPath(path.id)}
                    >
                      <Typography.Text style={{ color: "#f8fafc" }}>
                        Score {path.score}
                      </Typography.Text>
                      <Typography.Paragraph style={{ color: "#cbd5f5" }}>
                        {path.summary}
                      </Typography.Paragraph>
                    </Card>
                  ))}
                </div>
                <AttackGraph paths={paths} onSelectNode={selectNode} />
              </>
            )}
          </div>
          <div style={{ width: 320 }}>
            <AssetList onAssetSelect={handleAssetSelect} />
          </div>
        </div>
        <PathSummaryDrawer path={selectedPath} onClose={() => selectPath(undefined)} />
      </div>
    </div>
  );

  return (
    <div className="app-shell-vertical">
      <div className="header">
        <div>
          <Typography.Title level={3} style={{ color: "#f1f5f9", marginBottom: 0 }}>
            云原生攻击路径分析平台
          </Typography.Title>
          <Typography.Text style={{ color: "#94a3b8" }}>
            采集 Kubernetes 资产、构建图谱并可视化攻击路径
          </Typography.Text>
        </div>
        <HealthIndicator status={health} onRefresh={refreshHealth} />
      </div>
      <Tabs
        items={[
          { key: "paths", label: "攻击路径", children: pathTab },
          { key: "ingestion", label: "资产采集", children: <IngestionPanel /> },
          { key: "cypher", label: "Cypher 控制台", children: <CypherConsole /> }
        ]}
      />
    </div>
  );
};

export default App;
