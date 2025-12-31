import { useEffect } from "react";
import { Card, Empty, Spin, Typography } from "antd";
import { FilterPanel } from "./components/FilterPanel";
import { AttackGraph } from "./components/AttackGraph";
import { AssetList } from "./components/AssetList";
import { HealthIndicator } from "./components/HealthIndicator";
import { PathSummaryDrawer } from "./components/PathSummaryDrawer";
import { useAttackStore } from "./store/useAttackStore";
import { fetchHealth, searchAttackPaths } from "./services/api";

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
    setFilters(nextFilters);
    setLoading(true);
    try {
      const result = await searchAttackPaths(nextFilters);
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

  return (
    <div className="app-shell">
      <FilterPanel onSearch={handleSearch} />
      <div className="graph-container">
        <div className="header">
          <div>
            <Typography.Title level={3} style={{ color: "#f1f5f9", marginBottom: 0 }}>
              云原生攻击路径图谱
            </Typography.Title>
            <Typography.Text style={{ color: "#94a3b8" }}>
              直观展示攻击推进过程
            </Typography.Text>
          </div>
          <HealthIndicator status={health} onRefresh={refreshHealth} />
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <div style={{ flex: 1 }}>
            {loading ? (
              <Spin tip="计算路径..." />
            ) : paths.length === 0 ? (
              <Empty description="暂无路径结果" />
            ) : (
              <>
                <div
                  style={{
                    display: "flex",
                    gap: 12,
                    marginBottom: 12,
                    overflowX: "auto"
                  }}
                >
                  {paths.map((path) => (
                    <Card
                      key={path.id}
                      style={{
                        minWidth: 220,
                        backgroundColor:
                          path.id === selectedPathId ? "#1e293b" : "#111c3a",
                        color: "#f8fafc"
                      }}
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
                <AttackGraph
                  paths={paths}
                  onSelectNode={(nodeId) => selectNode(nodeId)}
                />
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
};

export default App;
