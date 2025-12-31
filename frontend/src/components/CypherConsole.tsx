import { useState } from "react";
import { Button, Card, Input, message, Space, Typography } from "antd";
import { executeCypher } from "../services/api";
import { CypherResult } from "../types";
import { CypherGraph } from "./CypherGraph";

const templates = [
  {
    label: "所有 Master 路径",
    query: "MATCH path = (s:Asset)-[:ATTACK_REL*1..4]->(t:Asset {type:'Master'}) RETURN path LIMIT 5"
  },
  {
    label: "高危 Secret",
    query: "MATCH (n:Asset {type:'Secret'}) WHERE n.criticality='HIGH' RETURN n LIMIT 10"
  }
];

export const CypherConsole = () => {
  const [query, setQuery] = useState(templates[0].query);
  const [result, setResult] = useState<CypherResult | null>(null);
  const [loading, setLoading] = useState(false);

  const runQuery = async () => {
    if (!query.trim()) {
      message.warning("请输入查询语句");
      return;
    }
    setLoading(true);
    try {
      const data = await executeCypher({ query });
      setResult(data);
    } catch (err) {
      message.error("查询失败，可能包含非法关键字");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card
        title="Cypher 查询"
        extra={
          <Space>
            {templates.map((tpl) => (
              <Button key={tpl.label} onClick={() => setQuery(tpl.query)}>
                {tpl.label}
              </Button>
            ))}
          </Space>
        }
      >
        <Input.TextArea
          rows={6}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <Button type="primary" onClick={runQuery} loading={loading}>
          执行
        </Button>
      </Card>

      {result ? (
        <Card
          title="图谱结果"
          extra={
            <Typography.Text style={{ color: "#94a3b8" }}>
              {result.nodes.length} 节点 · {result.edges.length} 关系
            </Typography.Text>
          }
        >
          <CypherGraph nodes={result.nodes} edges={result.edges} />
        </Card>
      ) : (
        <Typography.Paragraph style={{ color: "#94a3b8" }}>
          输入查询后将返回与 Neo4j Browser 一致的子图，可用于验证攻击路径。
        </Typography.Paragraph>
      )}
    </Space>
  );
};
