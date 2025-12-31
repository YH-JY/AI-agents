import { useEffect, useRef } from "react";
import cytoscape, { Core } from "cytoscape";
import { GraphEdge, GraphNode } from "../types";

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const typeColorMap: Record<string, string> = {
  Pod: "#2563eb",
  Container: "#0ea5e9",
  ServiceAccount: "#f97316",
  Secret: "#a855f7",
  Credential: "#facc15",
  Master: "#ef4444",
  Node: "#14b8a6",
  Volume: "#7c3aed"
};

export const CypherGraph = ({ nodes, edges }: Props) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    cyRef.current = cytoscape({
      container: containerRef.current,
      style: [
        {
          selector: "node",
          style: {
            "background-color": (ele) =>
              typeColorMap[ele.data("type")] ?? "#475569",
            label: "data(label)",
            color: "#e2e8f0",
            "text-wrap": "wrap"
          }
        },
        {
          selector: "edge",
          style: {
            width: 2,
            "target-arrow-shape": "triangle",
            "target-arrow-color": "#94a3b8",
            "line-color": "#475569",
            label: "data(label)",
            color: "#cbd5f5",
            "curve-style": "bezier"
          }
        }
      ]
    });
    return () => {
      cyRef.current?.destroy();
      cyRef.current = null;
    };
  }, []);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    cy.elements().remove();
    const nodeElements = nodes.map((node) => {
      const nodeType = node.type ?? (node.labels?.[0] as string | undefined);
      return {
        data: {
          id: node.id,
          label: node.name ? `${node.name}\n(${nodeType ?? ""})` : node.id,
          type: nodeType
        }
      };
    });
    const edgeElements = edges.map((edge) => {
      const technique =
        typeof edge.properties.technique === "string"
          ? edge.properties.technique
          : edge.type;
      return {
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: technique
        }
      };
    });
    cy.add([...nodeElements, ...edgeElements]);
    cy.layout({
      name: "breadthfirst",
      directed: true,
      spacingFactor: 1.4,
      animate: false,
      orientation: "LR"
    }).run();
    cy.fit(undefined, 20);
  }, [nodes, edges]);

  return <div className="cytoscape-wrapper" ref={containerRef} />;
};
