import { useEffect, useState } from "react";
import { Input, List, Select, Typography } from "antd";
import { fetchAssets } from "../services/api";
import { AssetSummary, NodeType } from "../types";

const nodeTypeOptions: NodeType[] = [
  "Container",
  "Pod",
  "Volume",
  "Node",
  "ServiceAccount",
  "Secret",
  "Credential",
  "Master"
];

interface Props {
  onAssetSelect: (assetId: string) => void;
}

export const AssetList = ({ onAssetSelect }: Props) => {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [type, setType] = useState<NodeType | undefined>();

  const fetchData = async () => {
    setLoading(true);
    try {
      const response = await fetchAssets({
        search: search || undefined,
        type,
        pageSize: 20
      });
      setAssets(response.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, type]);

  return (
    <div>
      <Typography.Title level={5} style={{ color: "#e2e8f0" }}>
        资产检索
      </Typography.Title>
      <Input.Search
        placeholder="按名称或 ID 搜索"
        allowClear
        onSearch={(value) => setSearch(value)}
      />
      <Select
        style={{ width: "100%", marginTop: 8 }}
        allowClear
        placeholder="类型筛选"
        onChange={(value) => setType(value as NodeType)}
      >
        {nodeTypeOptions.map((option) => (
          <Select.Option key={option} value={option}>
            {option}
          </Select.Option>
        ))}
      </Select>
      <List
        loading={loading}
        dataSource={assets}
        style={{ marginTop: 12 }}
        bordered
        renderItem={(item) => (
          <List.Item
            style={{ cursor: "pointer" }}
            onClick={() => onAssetSelect(item.id)}
          >
            <div>
              <Typography.Text style={{ color: "#f8fafc" }}>
                {item.name}
              </Typography.Text>
              <br />
              <Typography.Text style={{ color: "#94a3b8" }}>
                {item.type} · {item.namespace ?? "global"}
              </Typography.Text>
            </div>
          </List.Item>
        )}
      />
    </div>
  );
};
