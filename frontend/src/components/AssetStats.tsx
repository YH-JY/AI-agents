import { useEffect, useState } from "react";
import { Card, Col, Row, Typography } from "antd";
import { fetchAssetStats } from "../services/api";
import { AssetStats, NodeType } from "../types";

const typeColors: Record<NodeType, string> = {
  Pod: "#2563eb",
  Container: "#0ea5e9",
  Volume: "#7c3aed",
  Node: "#14b8a6",
  ServiceAccount: "#f97316",
  Secret: "#a855f7",
  Credential: "#facc15",
  Master: "#ef4444"
};

export const AssetStatsOverview = () => {
  const [stats, setStats] = useState<AssetStats[]>([]);

  useEffect(() => {
    fetchAssetStats().then((resp) => setStats(resp.stats));
  }, []);

  if (!stats.length) {
    return (
      <Typography.Text style={{ color: "#94a3b8" }}>
        暂无资产统计，先运行采集或导入示例数据。
      </Typography.Text>
    );
  }

  return (
    <Row gutter={[12, 12]}>
      {stats.map((stat) => (
        <Col xs={12} md={8} lg={6} key={stat.type}>
          <Card
            size="small"
            style={{
              borderColor: typeColors[stat.type] ?? "#1f2937",
              backgroundColor: "#111c3a"
            }}
          >
            <Typography.Text style={{ color: "#94a3b8" }}>
              {stat.type}
            </Typography.Text>
            <Typography.Title level={3} style={{ color: "#f8fafc", margin: 0 }}>
              {stat.total}
            </Typography.Title>
          </Card>
        </Col>
      ))}
    </Row>
  );
};
