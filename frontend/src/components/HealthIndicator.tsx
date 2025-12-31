import { Badge, Button } from "antd";
import { HealthStatus } from "../types";

interface Props {
  status?: HealthStatus;
  onRefresh: () => void;
}

export const HealthIndicator = ({ status, onRefresh }: Props) => {
  const ok = status?.neo4j === "up";
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12
      }}
    >
      <Badge
        status={ok ? "success" : "error"}
        text={
          ok
            ? `Neo4j ${status?.version ?? ""}`
            : "Neo4j Unavailable"
        }
        style={{ color: "#e2e8f0" }}
      />
      <Button type="link" onClick={onRefresh}>
        刷新
      </Button>
    </div>
  );
};
