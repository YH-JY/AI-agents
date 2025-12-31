import { Drawer, List, Typography, Button } from "antd";
import { AttackPath } from "../types";

interface Props {
  path?: AttackPath;
  onClose: () => void;
}

export const PathSummaryDrawer = ({ path, onClose }: Props) => {
  const handleExport = () => {
    if (!path) return;
    const blob = new Blob([JSON.stringify(path, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `attack-path-${path.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Drawer
      title="路径详情"
      placement="bottom"
      height="40%"
      open={Boolean(path)}
      onClose={onClose}
    >
      {path ? (
        <>
          <Typography.Title level={4}>评分：{path.score}</Typography.Title>
          <Typography.Paragraph>{path.summary}</Typography.Paragraph>
          <Button onClick={handleExport} type="primary" style={{ marginBottom: 12 }}>
            导出 JSON
          </Button>
          <List
            dataSource={path.steps}
            renderItem={(step) => (
              <List.Item>
                <div>
                  <Typography.Text strong>
                    Depth {step.depth}
                  </Typography.Text>
                  <Typography.Paragraph>
                    {step.nodes.map((node) => node.name).join(", ")}
                  </Typography.Paragraph>
                </div>
              </List.Item>
            )}
          />
        </>
      ) : (
        <Typography.Paragraph>未选择路径</Typography.Paragraph>
      )}
    </Drawer>
  );
};
