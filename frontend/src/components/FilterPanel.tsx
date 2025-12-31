import { useEffect } from "react";
import { Button, Form, Input, Select, Divider, Typography } from "antd";
import { AttackPathFilters } from "../services/api";
import { useAttackStore } from "../store/useAttackStore";
import { NodeType } from "../types";

const nodeTypeOptions = [
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
  onSearch: (filters: AttackPathFilters) => void;
}

export const FilterPanel = ({ onSearch }: Props) => {
  const [form] = Form.useForm();
  const filters = useAttackStore((state) => state.filters);

  useEffect(() => {
    form.setFieldsValue(filters);
  }, [filters, form]);

  const onFinish = (values: AttackPathFilters) => {
    onSearch({
      ...values,
      maxDepth: values.maxDepth ? Number(values.maxDepth) : undefined,
      limit: values.limit ? Number(values.limit) : undefined
    });
  };

  return (
    <div className="sidebar">
      <Typography.Title level={4} style={{ color: "#f8fafc" }}>
        过滤器
      </Typography.Title>
      <Form
        layout="vertical"
        form={form}
        initialValues={filters}
        onFinish={onFinish}
      >
        <Form.Item name="startNodeId" label="起始节点 ID">
          <Input placeholder="pod-frontend" allowClear />
        </Form.Item>
        <Form.Item name="startType" label="起始类型">
          <Select allowClear>
            {nodeTypeOptions.map((type) => (
              <Select.Option key={type} value={type}>
                {type}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item name="targetType" label="目标类型">
          <Select allowClear>
            {nodeTypeOptions.map((type) => (
              <Select.Option key={type} value={type}>
                {type}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item name="namespace" label="命名空间">
          <Input placeholder="prod" allowClear />
        </Form.Item>
        <Form.Item name="maxDepth" label="最大跳数" initialValue={6}>
          <Input type="number" min={1} max={8} />
        </Form.Item>
        <Form.Item name="limit" label="路径数量" initialValue={5}>
          <Input type="number" min={1} max={20} />
        </Form.Item>
        <Form.Item>
          <Button type="primary" htmlType="submit" block>
            计算路径
          </Button>
        </Form.Item>
      </Form>
      <Divider style={{ borderColor: "#1f2a44" }} />
      <Typography.Paragraph style={{ color: "#94a3b8" }}>
        通过指定起点或类型，平台会自动返回限定深度内的攻击路径。
      </Typography.Paragraph>
    </div>
  );
};
