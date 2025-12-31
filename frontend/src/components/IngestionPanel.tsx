import { useEffect, useState } from "react";
import {
  Button,
  Card,
  List,
  message,
  Segmented,
  Space,
  Table,
  Tag,
  Typography,
  Upload
} from "antd";
import type { UploadProps } from "antd";
import {
  listIngestionJobs,
  listKubeconfigs,
  runIngestion,
  uploadKubeconfig
} from "../services/api";
import { IngestionJob, IngestionMode, KubeConfigMetadata } from "../types";

const statusColor: Record<string, string> = {
  queued: "default",
  running: "processing",
  succeeded: "success",
  failed: "error"
};

export const IngestionPanel = () => {
  const [configs, setConfigs] = useState<KubeConfigMetadata[]>([]);
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<string>();
  const [mode, setMode] = useState<IngestionMode>("full");
  const [loading, setLoading] = useState(false);

  const fetchConfigs = async () => {
    const data = await listKubeconfigs();
    setConfigs(data);
    if (!selectedConfig && data.length > 0) {
      setSelectedConfig(data[0].id);
    }
  };

  const fetchJobs = async () => {
    const data = await listIngestionJobs();
    setJobs(data);
  };

  useEffect(() => {
    fetchConfigs();
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const uploadProps: UploadProps = {
    name: "file",
    multiple: false,
    showUploadList: false,
    customRequest: async (options) => {
      const { file, onSuccess, onError } = options;
      try {
        await uploadKubeconfig(file as File);
        message.success("上传 kubeconfig 成功");
        await fetchConfigs();
        onSuccess?.({}, new XMLHttpRequest());
      } catch (err) {
        onError?.(err as Error);
      }
    }
  };

  const handleRun = async () => {
    if (!selectedConfig) {
      message.warning("请选择 kubeconfig");
      return;
    }
    setLoading(true);
    try {
      await runIngestion({ configId: selectedConfig, mode });
      message.success("已启动采集任务");
      fetchJobs();
    } catch (err) {
      message.error("启动任务失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card title="上传 kubeconfig">
        <Upload.Dragger {...uploadProps}>
          <Typography.Paragraph>
            点击或拖拽 kubeconfig 文件，这些配置只会保存在本地 storage 目录。
          </Typography.Paragraph>
        </Upload.Dragger>
      </Card>

      <Card
        title="集群列表"
        extra={
          <Segmented
            options={[
              { label: "全量同步", value: "full" },
              { label: "增量同步", value: "incremental" }
            ]}
            value={mode}
            onChange={(value) => setMode(value as IngestionMode)}
          />
        }
      >
        <List
          dataSource={configs}
          locale={{ emptyText: "尚未上传 kubeconfig" }}
          renderItem={(item) => (
            <List.Item
              key={item.id}
              style={{
                cursor: "pointer",
                background: item.id === selectedConfig ? "#1e293b" : "transparent"
              }}
              onClick={() => setSelectedConfig(item.id)}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Typography.Text style={{ color: "#e2e8f0" }}>
                      {item.name}
                    </Typography.Text>
                    <Tag>{item.clusters.join(", ")}</Tag>
                  </Space>
                }
                description={
                  <Typography.Text style={{ color: "#94a3b8" }}>
                    {new Date(item.created_at).toLocaleString()}
                  </Typography.Text>
                }
              />
            </List.Item>
          )}
        />
        <Button
          type="primary"
          block
          style={{ marginTop: 16 }}
          loading={loading}
          onClick={handleRun}
          disabled={!configs.length}
        >
          运行采集
        </Button>
      </Card>

      <Card title="采集任务">
        <Table
          dataSource={jobs}
          rowKey="id"
          pagination={{ pageSize: 5 }}
          columns={[
            {
              title: "任务",
              dataIndex: "id",
              render: (value: string, record) => (
                <div>
                  <Typography.Text style={{ color: "#f8fafc" }}>
                    {record.config_name}
                  </Typography.Text>
                  <Typography.Paragraph style={{ color: "#94a3b8" }}>
                    {value}
                  </Typography.Paragraph>
                </div>
              )
            },
            {
              title: "模式",
              dataIndex: "mode"
            },
            {
              title: "状态",
              dataIndex: "status",
              render: (status: string) => (
                <Tag color={statusColor[status] ?? "default"}>{status}</Tag>
              )
            },
            {
              title: "开始",
              dataIndex: "started_at",
              render: (value: string | undefined) =>
                value ? new Date(value).toLocaleString() : "-"
            },
            {
              title: "结束",
              dataIndex: "finished_at",
              render: (value: string | undefined) =>
                value ? new Date(value).toLocaleString() : "-"
            },
            {
              title: "日志",
              dataIndex: "logs",
              render: (logs: string[]) => (
                <Typography.Paragraph style={{ color: "#94a3b8" }}>
                  {logs.length ? logs[logs.length - 1] : "无"}
                </Typography.Paragraph>
              )
            }
          ]}
        />
      </Card>
    </Space>
  );
};
