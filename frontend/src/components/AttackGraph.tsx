import { useEffect, useRef } from "react";
import cytoscape, { Core } from "cytoscape";
import { AttackPath } from "../types";

const typeColorMap: Record<string, string> = {
  Container: "#0ea5e9",
  Pod: "#2563eb",
  Volume: "#7c3aed",
  Node: "#14b8a6",
  ServiceAccount: "#f97316",
  Secret: "#a855f7",
  Credential: "#facc15",
  Master: "#ef4444"
};

interface Props {
  paths: AttackPath[];
  onSelectNode: (nodeId: string) => void;
}

export const AttackGraph = ({ paths, onSelectNode }: Props) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    if (!cyRef.current) {
      cyRef.current = cytoscape({
        container: containerRef.current,
        style: [
          {
            selector: "node",
            style: {
              "background-color": (ele) =>
                typeColorMap[ele.data("type")] ?? "#94a3b8",
              label: "data(label)",
              color: "#e2e8f0",
              "font-size": 12,
              "text-wrap": "wrap",
              "text-max-width": 120,
              "border-width": 1,
              "border-color": "#0f172a"
            }
          },
          {
            selector: "edge",
            style: {
              width: 2,
              "curve-style": "bezier",
              "target-arrow-shape": "triangle",
              "target-arrow-color": "#e2e8f0",
              "line-color": "#64748b",
              label: "data(label)",
              "font-size": 10,
              color: "#cbd5f5",
              "text-background-color": "#0b1121",
              "text-background-opacity": 0.8,
              "text-background-padding": 2
            }
          }
        ]
      });

      cyRef.current.on("tap", "node", (event) => {
        onSelectNode(event.target.id());
      });
    }

    return () => {
      cyRef.current?.destroy();
      cyRef.current = null;
    };
  }, [onSelectNode]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().remove();
    const elements = [];
    const seenNodes = new Set<string>();
    const seenEdges = new Set<string>();
    paths.forEach((path, pathIndex) => {
      path.steps.forEach((step, depth) => {
        step.nodes.forEach((node) => {
          if (seenNodes.has(node.id)) {
            return;
          }
          seenNodes.add(node.id);
          elements.push({
            data: {
              id: node.id,
              label: `${node.name}\n(${node.type})`,
              type: node.type,
              pathIndex,
              depth
            }
          });
        });
        step.edges.forEach((edge) => {
          const edgeId = `${edge.source}-${edge.target}-${pathIndex}`;
          if (seenEdges.has(edgeId)) {
            return;
          }
          seenEdges.add(edgeId);
          elements.push({
            data: {
              id: edgeId,
              source: edge.source,
              target: edge.target,
              label: edge.technique,
              pathIndex
            }
          });
        });
      });
    });
    cy.add(elements);
    cy.layout({
      name: "breadthfirst",
      directed: true,
      spacingFactor: 1.5,
      animate: false,
      grid: false,
      padding: 10,
      orientation: "LR"
    }).run();
    cy.fit(undefined, 20);
  }, [paths]);

  return <div className="cytoscape-wrapper" ref={containerRef} />;
};
