import { useState } from "react";
import { Button, Card, Input, message, Space, Table, Typography } from "antd";
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

      {result && (
        <>
          <Card title="图谱结果">
            <CypherGraph nodes={result.nodes} edges={result.edges} />
          </Card>
          <Card title="表格">
            <Table
              dataSource={result.table}
              rowKey={(_, idx) => idx.toString()}
              pagination={false}
              columns={
                result.table.length
                  ? Object.keys(result.table[0]).map((key) => ({
                      title: key,
                      dataIndex: key,
                      render: (value: unknown) =>
                        typeof value === "object"
                          ? JSON.stringify(value)
                          : String(value)
                    }))
                  : [{ title: "结果", dataIndex: "result" }]
              }
            />
          </Card>
        </>
      )}
      {!result && (
        <Typography.Paragraph style={{ color: "#94a3b8" }}>
          输入查询后将同时展示图谱与表格结果。
        </Typography.Paragraph>
      )}
    </Space>
  );
};
